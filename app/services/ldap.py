'''LDAP'''
from ldap3 import Server, Connection, ALL, Tls, AUTO_BIND_TLS_BEFORE_BIND, core, SUBTREE, ALL_ATTRIBUTES
from ssl import PROTOCOL_TLS_CLIENT
import yaml


class LDAP:
    def __init__(self):
        with open("conf/conf.yaml", "r") as yaml_file:
            self.data = yaml.load(yaml_file, Loader=yaml.FullLoader)

        try:
            self.tls = Tls(ca_certs_file=f"conf/{self.data['CA_FILE']}", version=PROTOCOL_TLS_CLIENT)
            self.server = Server(self.data["LDAP_SERVER"], get_info=ALL, tls=self.tls)
            self.conn = Connection(self.server, auto_bind=AUTO_BIND_TLS_BEFORE_BIND, raise_exceptions=True)
        except Exception as e:
            print("Exception in init: ", str(e))
            raise Exception


    def get_dn_of_user(self, username: str):
        try:
            self.conn.bind()
            self.conn.search(self.data["USER_BASE"], self.data["LDAP_SEARCH_FILTER"].format(name_attribute="uid", name=username))
            if self.conn.result['result'] == 0:
                self.user_dn = self.conn.response[0]['dn']
                return self.user_dn
            else:
                raise Exception
        except Exception as e:
            print("Exception in get_dn", str(e))
            raise Exception

    def get_home_dir(self, username: str):
        try:
            self.conn.bind()
            self.conn.search(self.data["USER_BASE"], self.data["LDAP_SEARCH_FILTER"].format(name_attribute="uid", name=username), search_scope=SUBTREE, attributes=ALL_ATTRIBUTES)
            if self.conn.entries:
                self.home_dir = self.conn.entries[0].homeDirectory.value
                return self.home_dir
        except Exception as e:
            print("Exception in get_home_dir", str(e))
            raise Exception

    def bind(self, dn: str, password: str):
        try:
            self.conn = Connection(self.server, dn, password, auto_bind=AUTO_BIND_TLS_BEFORE_BIND)
            return True
        except core.exceptions.LDAPBindError:
            print("User authentication failed.")
            raise Exception
