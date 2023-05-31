'''LDAP'''
from ldap3 import Server, Connection, ALL, Tls, AUTO_BIND_TLS_BEFORE_BIND, core
from ssl import PROTOCOL_TLSv1_2

LDAP_SERVER = 'ldap://ldap2.dieterichlab.org'
CA_FILE = 'DieterichLab_CA.pem'
USER_BASE = 'dc=dieterichlab,dc=org'
LDAP_SEARCH_FILTER = '({name_attribute}={name})'


try:
    tls = Tls(ca_certs_file=CA_FILE, version=PROTOCOL_TLSv1_2)
    server = Server(LDAP_SERVER, get_info=ALL, tls=tls)
    conn = Connection(server, auto_bind=AUTO_BIND_TLS_BEFORE_BIND, raise_exceptions=True)
except Exception as e:
    print("Exception in init: ", str(e))


def get_dn_of_user(username: str):
    try:
        conn.bind()
        conn.search(USER_BASE, LDAP_SEARCH_FILTER.format(name_attribute="uid", name=username))
        if conn.result['result'] == 0:
            user_dn = conn.response[0]['dn']
            return user_dn
        else:
            raise Exception
    except Exception as e:
        print("Exception in get_dn", str(e))


def bind(dn: str, password: str):
    try:
        conn = Connection(server, dn, password, auto_bind=AUTO_BIND_TLS_BEFORE_BIND)
        return True
    except core.exceptions.LDAPBindError:
        print("User authentication failed.")
        return False
