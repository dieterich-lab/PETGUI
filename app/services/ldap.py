'''LDAP'''
from ldap3 import Server, Connection, ALL, Tls, AUTO_BIND_TLS_BEFORE_BIND, core
from ssl import PROTOCOL_TLS_CLIENT
import yaml

with open("conf.yaml", "r") as yaml_file:
    data = yaml.load(yaml_file, Loader=yaml.FullLoader)

try:
    tls = Tls(ca_certs_file=data["CA_FILE"], version=PROTOCOL_TLS_CLIENT)
    server = Server(data["LDAP_SERVER"], get_info=ALL, tls=tls)
    conn = Connection(server, auto_bind=AUTO_BIND_TLS_BEFORE_BIND, raise_exceptions=True)
except Exception as e:
    print("Exception in init: ", str(e))
    raise Exception


def get_dn_of_user(username: str):
    try:
        conn.bind()
        conn.search(data["USER_BASE"], data["LDAP_SEARCH_FILTER"].format(name_attribute="uid", name=username))
        if conn.result['result'] == 0:
            user_dn = conn.response[0]['dn']
            return user_dn
        else:
            raise Exception
    except Exception as e:
        print("Exception in get_dn", str(e))
        raise Exception


def bind(dn: str, password: str):
    try:
        conn = Connection(server, dn, password, auto_bind=AUTO_BIND_TLS_BEFORE_BIND)
        return True
    except core.exceptions.LDAPBindError:
        print("User authentication failed.")
        raise Exception
