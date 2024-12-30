from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List


class RmResponse(BaseModel):
    notes: List[str] = []


class RmScriptResponse(BaseModel):
    script: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class RmKeyValue(BaseModel):
    key: str
    value: str


class RmInformation(BaseModel):
    name: str
    record_type: str
    version: Optional[str] = None
    version_number: Optional[str] = None
    supports_groups: bool = False
    supports_roles: bool = False
    can_create_users: bool = False
    can_delete_users: bool = False
    can_run_scripts: bool = False
    settings: List[RmKeyValue] = []


class RmUser(BaseModel):
    id: str
    name: str
    desc: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None
    connect_database: Optional[str] = None
    dn: Optional[str] = None


class RmNewUser(BaseModel):
    id: str
    name: str
    desc: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None
    connect_database: Optional[str] = None
    dn: Optional[str] = None


class RmRole(BaseModel):
    id: str
    name: Optional[str] = None
    desc: Optional[str] = None
    users: List[RmUser] = []


class RmGroup(BaseModel):
    id: str
    name: Optional[str] = None
    desc: Optional[str] = None
    users: List[RmUser] = []


class RmStubMeta(BaseModel):
    pass


class RmAwsUserAddMeta(BaseModel):
    console_access:  Optional[bool] = True
    path: Optional[str] = "/"
    permission_boundary_arn: Optional[str] = None
    password_reset_required: Optional[bool] = False
    tags: List[RmKeyValue] = []
    roles: List[str] = []
    groups: List[str] = []
    policies: List[str] = []


class RmAzureUserAddMeta(BaseModel):
    account_enabled: Optional[bool] = True
    display_name: Optional[str] = None
    on_premise_immutable_id: Optional[str] = None
    password_reset_required: Optional[bool] = False
    password_reset_reqiured_with_mfa: Optional[bool] = False
    roles: List[str] = []
    groups: List[str] = []


class RmDomainUserAddMeta(BaseModel):
    roles: List[str] = []
    groups: List[str] = []


class RmMySQLUserAddMeta(BaseModel):
    authentication_plugin: Optional[str] = None
    authentication_value: Optional[str] = None
    roles: List[str] = []


class RmPostgreSqlUserAddMeta(BaseModel):
    superuser: Optional[bool] = False
    create_db: Optional[bool] = False
    create_role: Optional[bool] = False
    inherit: Optional[bool] = False
    login: Optional[bool] = True
    replication: Optional[bool] = False
    bypass_rls: Optional[bool] = False
    connection_limit: Optional[int] = None
    valid_until: Optional[str] = None
    roles: List[str] = []
    inc_in_roles: List[str] = []
    inc_in_roles_as_admin: List[str] = []
    sysid: Optional[str] = None


# MACHINE


class RmLinuxUserAddMeta(BaseModel):
    system_user: Optional[bool] = False
    shell: Optional[str] = None
    no_login:  Optional[bool] = False
    home_dir: Optional[str] = None
    do_not_create_home_dir: Optional[bool] = False
    allow_bad_names: Optional[bool] = False
    gecos_full_name: Optional[str] = None
    gecos_room_number: Optional[str] = None
    gecos_work_phone: Optional[str] = None
    gecos_home_phone: Optional[str] = None
    gecos_other: Optional[str] = None
    group: Optional[str] = None
    groups: List[str] = []
    create_group: Optional[bool] = False
    validate_group: Optional[bool] = True
    uid: Optional[str] = None
    selinux_user_context:  Optional[str] = None
    btrfs_subvolume: Optional[bool] = False
    system_dir_mode: Optional[str] = None
    non_system_dir_mode: Optional[str] = None
    use_password: Optional[bool] = True
    use_private_key: Optional[bool] = False
    use_private_key_type: Optional[str] = "ecdsa_sha2_nistp521"
    private_key: Optional[str] = None
    authorized_keys: List[str] = []


class RmLinuxUserDeleteMeta(BaseModel):
    remove_home_dir: Optional[bool] = False
    remove_user_group: Optional[bool] = True


# DIRECTORY


class RmBaseLdapUserAddMeta(BaseModel):
    object_class: List[str] = []
    cn: Optional[str] = None
    dn: Optional[str] = None
    base_dn: Optional[str] = None
    auto_uid_number: bool = True
    gid_number_match_uid: bool = True
    home_dir_base: Optional[str] = "/home"
    first_rdn_component: Optional[str] = None
    attributes: Optional[dict] = {}
    groups: List[str] = []


class RmOpenLdapUserAddMeta(RmBaseLdapUserAddMeta):
    object_class: List[str] = ["top", "inetOrgPerson", "posixAccount"]


class RmAdUserAddMeta(RmBaseLdapUserAddMeta):
    object_class: List[str] = ["top", "person", "organizationalPerson", "user"]
    user_account_control: Optional[int] = 512


class RmBaseLdapUserDeleteMeta(BaseModel):
    orphan_check: Optional[bool] = True
    delete_orphans: Optional[bool] = False
