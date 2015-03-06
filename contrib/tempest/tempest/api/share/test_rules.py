# Copyright 2014 Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest_lib import exceptions as lib_exc  # noqa
import testtools  # noqa

from tempest.api.share import base
from tempest import config_share as config
from tempest import test

CONF = config.CONF


def _create_delete_ro_access_rule(self):
    """Common test case for usage in test suites with different decorators.

    :param self: instance of test class
    """
    resp, rule = self.shares_client.create_access_rule(
        self.share["id"], 'ip', '2.2.2.2', 'ro')
    self.assertIn(int(resp["status"]), self.HTTP_SUCCESS)
    self.assertEqual('ro', rule['access_level'])
    self.shares_client.wait_for_access_rule_status(
        self.share["id"], rule["id"], "active")
    resp, _ = self.shares_client.delete_access_rule(
        self.share["id"], rule["id"])
    self.assertIn(int(resp["status"]), self.HTTP_SUCCESS)


class ShareIpRulesForNFSTest(base.BaseSharesTest):
    protocol = "nfs"

    @classmethod
    def resource_setup(cls):
        super(ShareIpRulesForNFSTest, cls).resource_setup()
        if (cls.protocol not in CONF.share.enable_protocols or
                cls.protocol not in CONF.share.enable_ip_rules_for_protocols):
            msg = "IP rule tests for %s protocol are disabled" % cls.protocol
            raise cls.skipException(msg)
        __, cls.share = cls.create_share(cls.protocol)

    @test.attr(type=["gate", ])
    def test_create_delete_access_rules_with_one_ip(self):

        # test data
        access_type = "ip"
        access_to = "1.1.1.1"

        # create rule
        resp, rule = self.shares_client.create_access_rule(self.share["id"],
                                                           access_type,
                                                           access_to)
        self.assertIn(int(resp["status"]), self.HTTP_SUCCESS)
        self.assertEqual('rw', rule['access_level'])
        self.shares_client.wait_for_access_rule_status(self.share["id"],
                                                       rule["id"],
                                                       "active")
        # delete rule
        resp, _ = self.shares_client.delete_access_rule(self.share["id"],
                                                        rule["id"])
        self.assertIn(int(resp["status"]), self.HTTP_SUCCESS)

    @test.attr(type=["gate", ])
    def test_create_delete_access_rule_with_cidr(self):

        # test data
        access_type = "ip"
        access_to = "1.2.3.4/32"

        # create rule
        resp, rule = self.shares_client.create_access_rule(self.share["id"],
                                                           access_type,
                                                           access_to)
        self.assertIn(int(resp["status"]), self.HTTP_SUCCESS)
        self.assertEqual('rw', rule['access_level'])
        self.shares_client.wait_for_access_rule_status(self.share["id"],
                                                       rule["id"],
                                                       "active")
        # delete rule
        resp, _ = self.shares_client.delete_access_rule(self.share["id"],
                                                        rule["id"])
        self.assertIn(int(resp["status"]), self.HTTP_SUCCESS)

    @test.attr(type=["gate", ])
    @testtools.skipIf(
        "nfs" not in CONF.share.enable_ro_access_level_for_protocols,
        "RO access rule tests are disabled for NFS protocol.")
    def test_create_delete_ro_access_rule(self):
        _create_delete_ro_access_rule(self)


class ShareIpRulesForCIFSTest(ShareIpRulesForNFSTest):
    protocol = "cifs"

    @test.attr(type=["gate", ])
    @testtools.skipIf(
        "cifs" not in CONF.share.enable_ro_access_level_for_protocols,
        "RO access rule tests are disabled for CIFS protocol.")
    def test_create_delete_ro_access_rule(self):
        _create_delete_ro_access_rule(self)


class ShareUserRulesForNFSTest(base.BaseSharesTest):
    protocol = "nfs"

    @classmethod
    def resource_setup(cls):
        super(ShareUserRulesForNFSTest, cls).resource_setup()
        if (cls.protocol not in CONF.share.enable_protocols or
                cls.protocol not in
                CONF.share.enable_user_rules_for_protocols):
            msg = "USER rule tests for %s protocol are disabled" % cls.protocol
            raise cls.skipException(msg)
        __, cls.share = cls.create_share(cls.protocol)
        cls.access_type = "user"
        cls.access_to = CONF.share.username_for_user_rules

    @test.attr(type=["gate", ])
    def test_create_delete_user_rule(self):
        # create rule
        resp, rule = self.shares_client.create_access_rule(self.share["id"],
                                                           self.access_type,
                                                           self.access_to)
        self.assertIn(int(resp["status"]), self.HTTP_SUCCESS)
        self.assertEqual('rw', rule['access_level'])
        self.shares_client.wait_for_access_rule_status(self.share["id"],
                                                       rule["id"],
                                                       "active")
        # delete rule
        resp, _ = self.shares_client.delete_access_rule(self.share["id"],
                                                        rule["id"])
        self.assertIn(int(resp["status"]), self.HTTP_SUCCESS)

    @test.attr(type=["gate", ])
    @testtools.skipIf(
        "nfs" not in CONF.share.enable_ro_access_level_for_protocols,
        "RO access rule tests are disabled for NFS protocol.")
    def test_create_delete_ro_access_rule(self):
        _create_delete_ro_access_rule(self)


class ShareUserRulesForCIFSTest(ShareUserRulesForNFSTest):
    protocol = "cifs"

    @test.attr(type=["gate", ])
    @testtools.skipIf(
        "cifs" not in CONF.share.enable_ro_access_level_for_protocols,
        "RO access rule tests are disabled for CIFS protocol.")
    def test_create_delete_ro_access_rule(self):
        _create_delete_ro_access_rule(self)


class ShareRulesTest(base.BaseSharesTest):

    @classmethod
    def resource_setup(cls):
        super(ShareRulesTest, cls).resource_setup()
        if not (any(p in CONF.share.enable_ip_rules_for_protocols
                    for p in cls.protocols) or
                any(p in CONF.share.enable_user_rules_for_protocols
                    for p in cls.protocols)):
            cls.message = "Rule tests are disabled"
            raise cls.skipException(cls.message)
        __, cls.share = cls.create_share()

    def setUp(self):
        # Here we choose protocol and rule type for
        # testing common rules functionality,
        # that isn't dependent on protocol or rule type.
        super(ShareRulesTest, self).setUp()
        if CONF.share.enable_ip_rules_for_protocols:
            self.access_type = "ip"
            self.access_to = "8.8.8.8"
            protocol = CONF.share.enable_ip_rules_for_protocols[0]
        elif CONF.share.enable_user_rules_for_protocols:
            self.access_type = "user"
            self.access_to = CONF.share.username_for_user_rules
            protocol = CONF.share.enable_user_rules_for_protocols[0]
        else:
            raise self.skipException(self.message)
        self.shares_client.protocol = protocol

    @test.attr(type=["gate", ])
    def test_list_access_rules(self):

        # create rule
        resp, rule = self.shares_client.create_access_rule(self.share["id"],
                                                           self.access_type,
                                                           self.access_to)

        self.assertIn(int(resp["status"]), self.HTTP_SUCCESS)
        self.shares_client.wait_for_access_rule_status(self.share["id"],
                                                       rule["id"],
                                                       "active")

        # list rules
        resp, rules = self.shares_client.list_access_rules(self.share["id"])

        # verify response
        msg = "We expected status 200, but got %s" % (str(resp["status"]))
        self.assertEqual(200, int(resp["status"]), msg)

        # verify keys
        keys = ["state", "id", "access_type", "access_to", "access_level"]
        [self.assertIn(key, r.keys()) for r in rules for key in keys]

        # verify values
        self.assertEqual("active", rules[0]["state"])
        self.assertEqual(self.access_type, rules[0]["access_type"])
        self.assertEqual(self.access_to, rules[0]["access_to"])
        self.assertEqual('rw', rules[0]["access_level"])

        # our share id in list and have no duplicates
        gen = [r["id"] for r in rules if r["id"] in rule["id"]]
        msg = "expected id lists %s times in rule list" % (len(gen))
        self.assertEqual(len(gen), 1, msg)

    @test.attr(type=["gate", ])
    def test_access_rules_deleted_if_share_deleted(self):

        # create share
        __, share = self.create_share()

        # create rule
        resp, rule = self.shares_client.create_access_rule(share["id"],
                                                           self.access_type,
                                                           self.access_to)
        self.assertIn(int(resp["status"]), self.HTTP_SUCCESS)
        self.shares_client.wait_for_access_rule_status(share["id"], rule["id"],
                                                       "active")

        # delete share
        resp, _ = self.shares_client.delete_share(share['id'])
        self.assertIn(int(resp["status"]), self.HTTP_SUCCESS)
        self.shares_client.wait_for_resource_deletion(share_id=share['id'])

        # verify absence of rules for nonexistent share id
        self.assertRaises(lib_exc.NotFound,
                          self.shares_client.list_access_rules,
                          share['id'])
