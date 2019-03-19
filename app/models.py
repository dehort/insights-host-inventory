import uuid

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import orm

from app.exceptions import InputFormatException

from app.validators import (validate_string,
                            validate_ip_address_list,
                            validate_mac_address_list)
from api.json_validators import verify_uuid_format

db = SQLAlchemy()


CANONICAL_FACTS = (
    ("insights_id", verify_uuid_format),
    ("rhel_machine_id", verify_uuid_format),
    ("subscription_manager_id", verify_uuid_format),
    ("satellite_id", verify_uuid_format),
    ("bios_uuid", verify_uuid_format),
    ("ip_addresses", validate_ip_address_list),
    ("fqdn", validate_string(max_length=200)),
    ("mac_addresses", validate_mac_address_list),
    ("external_id", validate_string(max_length=200)),
)


def convert_fields_to_canonical_facts(json_dict):
    canonical_fact_list = {}
    for (cf_key, validator) in CANONICAL_FACTS:
        print("cf_key:", cf_key)
        print("validator:", validator)
        # Do not allow the incoming canonical facts to be None or ''
        if cf_key in json_dict and json_dict[cf_key]:
            print("Calling validator:", cf_key)
            if validator(json_dict[cf_key]):
                print("VALID")
                canonical_fact_list[cf_key] = json_dict[cf_key]
            else:
                print("INVALID")
                raise InputFormatException(f"Invalid format of {cf_key} field")
    return canonical_fact_list


def convert_canonical_facts_to_fields(internal_dict):
    canonical_fact_dict = dict.fromkeys([cf[0] for cf in CANONICAL_FACTS], None)
    #print("canonical_fact_dict:", canonical_fact_dict)
    for (cf, _) in CANONICAL_FACTS:
        if cf in internal_dict:
            canonical_fact_dict[cf] = internal_dict[cf]
    #print("canonical_fact_dict:", canonical_fact_dict)
    return canonical_fact_dict


def convert_json_facts_to_dict(fact_list):
    fact_dict = {}
    for fact in fact_list:
        if "namespace" in fact and "facts" in fact:
            if fact["namespace"] in fact_dict:
                fact_dict[fact["namespace"]].update(fact["facts"])
            else:
                fact_dict[fact["namespace"]] = fact["facts"]
        else:
            # The facts from the request are formatted incorrectly
            raise InputFormatException("Invalid format of Fact object.  Fact "
                                       "must contain 'namespace' and 'facts' keys.")
    return fact_dict


def convert_dict_to_json_facts(fact_dict):
    fact_list = [
        {"namespace": namespace, "facts": facts if facts else {}}
        for namespace, facts in fact_dict.items()
    ]
    return fact_list


def _set_display_name_on_save(context):
    """
    This method sets the display_name if it has not been set previously.
    This logic happens during the saving of the host record so that
    the id exists and can be used as the display_name if necessary.
    """
    params = context.get_current_parameters()
    if not params['display_name']:
        return params["canonical_facts"].get("fqdn") or params['id']


class Host(db.Model):
    __tablename__ = "hosts"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account = db.Column(db.String(10))
    display_name = db.Column(db.String(200), default=_set_display_name_on_save)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    modified_on = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    facts = db.Column(JSONB)
    tags = db.Column(JSONB)
    canonical_facts = db.Column(JSONB)

    def __init__(
        self,
        canonical_facts,
        display_name=display_name,
        account=account,
        facts=None,
    ):
        self.canonical_facts = canonical_facts
        if display_name:
            # Only set the display_name field if input the display_name has
            # been set...this will make it so that the "default" logic will
            # get called during the save to fill in an empty display_name
            self.display_name = display_name
        self.account = account
        self.facts = facts

    @classmethod
    def from_json(cls, d):
        return cls(
            # Internally store the canonical facts as a dict
            convert_fields_to_canonical_facts(d),
            #validate_string(d.get("display_name", None), min_length=1, max_length=200),
            d.get("display_name", None),
            d.get("account"),
            #validate_string(d.get("account"), min_length=1, max_length=20),
            # Internally store the facts in a dict
            convert_json_facts_to_dict(d.get("facts", [])),
        )

    def to_json(self):
        json_dict = convert_canonical_facts_to_fields(self.canonical_facts)
        json_dict["id"] = self.id
        json_dict["account"] = self.account
        json_dict["display_name"] = self.display_name
        # Internally store the facts in a dict
        json_dict["facts"] = convert_dict_to_json_facts(self.facts)
        json_dict["created"] = self.created_on
        json_dict["updated"] = self.modified_on
        return json_dict

    def save(self):
        db.session.add(self)

    def update(self, input_host):
        self.update_canonical_facts(input_host.canonical_facts)

        self.update_display_name(input_host)

        self.update_facts(input_host.facts)

    def update_display_name(self, input_host):
        if input_host.display_name:
            self.display_name = input_host.display_name
        elif not self.display_name:
            # This is the case where the display_name is not set on the
            # existing host record and the input host does not have it set
            if "fqdn" in self.canonical_facts:
                self.display_name = self.canonical_facts["fqdn"]
            else:
                self.display_name = self.id

    def update_canonical_facts(self, canonical_facts):
        self.canonical_facts.update(canonical_facts)
        orm.attributes.flag_modified(self, "canonical_facts")

    def update_facts(self, facts_dict):
        if facts_dict:
            if not self.facts:
                self.facts = facts_dict
                return

            for input_namespace, input_facts in facts_dict.items():
                self.replace_facts_in_namespace(input_namespace, input_facts)

    def replace_facts_in_namespace(self, namespace, facts_dict):
        self.facts[namespace] = facts_dict
        orm.attributes.flag_modified(self, "facts")

    def merge_facts_in_namespace(self, namespace, facts_dict):
        if not facts_dict:
            return

        if self.facts[namespace]:
            self.facts[namespace] = {**self.facts[namespace], **facts_dict}
        else:
            # The value currently stored in the namespace is None so replace it
            self.facts[namespace] = facts_dict
        orm.attributes.flag_modified(self, "facts")

    def __repr__(self):
        tmpl = "<Host '%s' '%s' canonical_facts=%s facts=%s>"
        return tmpl % (
            self.display_name,
            self.id,
            self.canonical_facts,
            self.facts,
        )
