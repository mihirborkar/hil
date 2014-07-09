"""Unit tests for api.py"""

from haas import model, api
from haas.test_common import newDB, releaseDB
import pytest

from haas.config import cfg

# Use the 'null' backend for these tests
cfg.add_section('general')
cfg.set('general', 'active_switch', 'null')

class TestGroup:
    """Tests for the haas.api.group_* functions."""

    # Several basic tests, functions should succeed in trivial cases.
    def test_group_create(self):
        db = newDB()
        api.group_create('acme-corp')
        api._must_find(db, model.Group, 'acme-corp')
        releaseDB(db)

    def test_group_add_user(self):
        db = newDB()
        api.user_create('alice', 'secret')
        api.group_create('acme-corp')
        api.group_add_user('acme-corp', 'alice')
        user = api._must_find(db, model.User, 'alice')
        group = api._must_find(db, model.Group, 'acme-corp')
        assert group in user.groups
        assert user in group.users
        releaseDB(db)

    def test_group_remove_user(self):
        db = newDB()
        api.user_create('alice', 'secret')
        api.group_create('acme-corp')
        api.group_add_user('acme-corp', 'alice')
        api.group_remove_user('acme-corp', 'alice')
        user = api._must_find(db, model.User, 'alice')
        group = api._must_find(db, model.Group, 'acme-corp')
        assert group not in user.groups
        assert user not in group.users
        releaseDB(db)

    def test_group_delete(self):
        db = newDB()
        api.group_create('acme-corp')
        api.group_delete('acme-corp')
        with pytest.raises(api.NotFoundError):
            api._must_find(db, model.Group, 'acme-corp')
        releaseDB(db)

    # Error handling tests:
    def test_duplicate_group_create(self):
        db = newDB()
        api.group_create('acme-corp')
        with pytest.raises(api.DuplicateError):
            api.group_create('acme-corp')
        releaseDB(db)

    def test_duplicate_group_add_user(self):
        db = newDB()
        api.user_create('alice', 'secret')
        api.group_create('acme-corp')
        api.group_add_user('acme-corp', 'alice')
        with pytest.raises(api.DuplicateError):
            api.group_add_user('acme-corp', 'alice')
        releaseDB(db)

    def test_bad_group_remove_user(self):
        """Tests that removing a user from a group they're not in fails."""
        db = newDB()
        api.user_create('alice', 'secret')
        api.group_create('acme-corp')
        with pytest.raises(api.NotFoundError):
            api.group_remove_user('acme-corp', 'alice')
        releaseDB(db)

class TestUser:
    """Tests for the haas.api.user_* functions."""

    def test_new_user(self):
        db = newDB()
        api._assert_absent(db, model.User, 'bob')
        api.user_create('bob', 'foo')
        releaseDB(db)

    def test_duplicate_user(self):
        db = newDB()
        api.user_create('alice', 'secret')
        with pytest.raises(api.DuplicateError):
                api.user_create('alice', 'password')
        releaseDB(db)

    def test_delete_user(self):
        db = newDB()
        api.user_create('bob', 'foo')
        api.user_delete('bob')
        releaseDB(db)

    def test_delete_missing_user(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.user_delete('bob')
        releaseDB(db)

    def test_delete_user_twice(self):
        db = newDB()
        api.user_create('bob', 'foo')
        api.user_delete('bob')
        with pytest.raises(api.NotFoundError):
            api.user_delete('bob')
        releaseDB(db)


class TestProjectCreateDelete:
    """Tests for the haas.api.project_* functions."""

    def test_project_create_success(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        api._must_find(db, model.Project, 'anvil-nextgen')
        releaseDB(db)

    def test_project_create_duplicate(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        with pytest.raises(api.DuplicateError):
            api.project_create('anvil-nextgen', 'acme-corp')
        releaseDB(db)

    def test_project_delete(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        api.project_delete('anvil-nextgen')
        with pytest.raises(api.NotFoundError):
            api._must_find(db, model.Project, 'anvil-nextgen')
        releaseDB(db)

    def test_project_delete_nexist(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.project_delete('anvil-nextgen')
        releaseDB(db)

class TestProjectConnectDetachNode:

    def test_project_connect_node(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        api.node_register('node-99')
        api.project_connect_node('anvil-nextgen', 'node-99')
        project = api._must_find(db, model.Project, 'anvil-nextgen')
        node = api._must_find(db, model.Node, 'node-99')
        assert node in project.nodes
        assert node.project is project
        releaseDB(db)

    def test_project_connect_node_project_nexist(self):
        """Tests that connecting a node to a nonexistent project fails"""
        db = newDB()
        api.node_register('node-99')
        with pytest.raises(api.NotFoundError):
            api.project_connect_node('anvil-nextgen', 'node-99')
        releaseDB(db)

    def test_project_connect_node_node_nexist(self):
        """Tests that connecting a nonexistent node to a projcet fails"""
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        with pytest.raises(api.NotFoundError):
            api.project_connect_node('anvil-nextgen', 'node-99')
        releaseDB(db)

    def test_project_detach_node(self):
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        api.node_register('node-99')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_detach_node('anvil-nextgen', 'node-99')
        project = api._must_find(db, model.Project, 'anvil-nextgen')
        node = api._must_find(db, model.Node, 'node-99')
        assert node not in project.nodes
        assert node.project is not project
        releaseDB(db)

    def test_project_detach_node_notattached(self):
        """Tests that removing a node from a project it's not in fails."""
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        api.node_register('node-99')
        with pytest.raises(api.NotFoundError):
            api.project_detach_node('anvil-nextgen', 'node-99')
        releaseDB(db)

    def test_project_detach_node_project_nexist(self):
        """Tests that removing a node from a nonexistent project fails."""
        db = newDB()
        api.node_register('node-99')
        with pytest.raises(api.NotFoundError):
            api.project_detach_node('anvil-nextgen', 'node-99')
        releaseDB(db)

    def test_project_detach_node_node_nexist(self):
        """Tests that removing a nonexistent node from a project fails."""
        db = newDB()
        api.group_create('acme-corp')
        api.project_create('anvil-nextgen', 'acme-corp')
        with pytest.raises(api.NotFoundError):
            api.project_detach_node('anvil-nextgen', 'node-99')
        releaseDB(db)


class TestNodeRegisterDelete:
    """Tests for the haas.api.node_* functions."""

    def test_node_register(self):
        db = newDB()
        api.node_register('node-99')
        api._must_find(db, model.Node, 'node-99')
        releaseDB(db)

    def test_duplicate_node_register(self):
        db = newDB()
        api.node_register('node-99')
        with pytest.raises(api.DuplicateError):
            api.node_register('node-99')
        releaseDB(db)

    def test_node_delete(self):
        db = newDB()
        api.node_register('node-99')
        api.node_delete('node-99')
        with pytest.raises(api.NotFoundError):
            api._must_find(db, model.Node, 'node-99')
        releaseDB(db)

    def test_node_delete_nexist(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.node_delete('node-99')
        releaseDB(db)


class TestNodeRegisterDeleteNic:

    def test_node_register_nic(self):
        db = newDB()
        api.node_register('compute-01')
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        nic = api._must_find(db, model.Nic, '01-eth0')
        assert nic.node.label == 'compute-01'
        releaseDB(db)

    def test_node_register_nic_no_node(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        releaseDB(db)

    def test_node_register_nic_duplicate_nic(self):
        db = newDB()
        api.node_register('compute-01')
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        nic = api._must_find(db, model.Nic, '01-eth0')
        with pytest.raises(api.DuplicateError):
            api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:15')
        releaseDB(db)

    def test_node_delete_nic_success(self):
        db = newDB()
        api.node_register('compute-01')
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        api.node_delete_nic('compute-01', '01-eth0')
        api._assert_absent(db, model.Nic, '01-eth0')
        api._must_find(db, model.Node, 'compute-01')
        releaseDB(db)

    def test_node_delete_nic_nic_nexist(self):
        db = newDB()
        api.node_register('compute-01')
        with pytest.raises(api.NotFoundError):
            api.node_delete_nic('compute-01', '01-eth0')
        releaseDB(db)

    def test_node_delete_nic_node_nexist(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.node_delete_nic('compute-01', '01-eth0')
        releaseDB(db)

    def test_node_delete_nic_wrong_node(self):
        db = newDB()
        api.node_register('compute-01')
        api.node_register('compute-02')
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.node_delete_nic('compute-02', '01-eth0')
        releaseDB(db)

    def test_node_delete_nic_wrong_nexist_node(self):
        db = newDB()
        api.node_register('compute-01')
        api.node_register_nic('compute-01', '01-eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.node_delete_nic('compute-02', '01-eth0')
        releaseDB(db)


class TestNodeConnectDetachNetwork:

    def test_node_connect_network_success(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.network_create('hammernet', 'anvil-nextgen')

        api.node_connect_network('node-99', '99-eth0', 'hammernet')
        network = api._must_find(db, model.Network, 'hammernet')
        nic = api._must_find(db, model.Nic, '99-eth0')
        assert nic.network is network
        assert nic in network.nics
        releaseDB(db)

    def test_node_connect_network_wrong_node_in_project(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.network_create('hammernet', 'anvil-nextgen')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')
        api.node_register('node-98') #added
        api.project_connect_node('anvil-nextgen', 'node-98') #added

        with pytest.raises(api.NotFoundError):
            api.node_connect_network('node-98', '99-eth0', 'hammernet')
        releaseDB(db)

    def test_node_connect_network_wrong_node_not_in_project(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.network_create('hammernet', 'anvil-nextgen')
        api.node_register('node-98') # added

        with pytest.raises(api.NotFoundError):
            api.node_connect_network('node-98', '99-eth0', 'hammernet')
        releaseDB(db)

    def test_node_connect_network_no_such_node(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.network_create('hammernet', 'anvil-nextgen')

        with pytest.raises(api.NotFoundError):
            api.node_connect_network('node-98', '99-eth0', 'hammernet') # changed
        releaseDB(db)

    def test_node_connect_network_no_such_nic(self):
        db = newDB()
        api.node_register('node-99')
#        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.network_create('hammernet', 'anvil-nextgen')

        with pytest.raises(api.NotFoundError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')
        releaseDB(db)

    def test_node_connect_network_no_such_network(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
#        api.network_create('hammernet', 'anvil-nextgen')
        with pytest.raises(api.NotFoundError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')
        releaseDB(db)

    def test_node_connect_network_already_attached_to_same(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.network_create('hammernet', 'anvil-nextgen')
        api.node_connect_network('node-99', '99-eth0', 'hammernet') # added

        with pytest.raises(api.DuplicateError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet')
        releaseDB(db)

    def test_node_connect_network_already_attached_differently(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.network_create('hammernet', 'anvil-nextgen')
        api.network_create('hammernet2', 'anvil-nextgen') #added
        api.node_connect_network('node-99', '99-eth0', 'hammernet') # added

        with pytest.raises(api.DuplicateError):
            api.node_connect_network('node-99', '99-eth0', 'hammernet2')
        releaseDB(db)


    def test_node_detach_network_success(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.network_create('hammernet', 'anvil-nextgen')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        api.node_detach_network('node-99', '99-eth0')
        network = api._must_find(db, model.Network, 'hammernet')
        nic = api._must_find(db, model.Nic, '99-eth0')
        assert nic.network is not network
        assert nic not in network.nics
        releaseDB(db)

    def test_node_detach_network_not_attached(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.network_create('hammernet', 'anvil-nextgen')
#        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.node_detach_network('node-99', '99-eth0')
        releaseDB(db)

    def test_node_detach_network_wrong_node_in_project(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register('node-98') # added
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.project_connect_node('anvil-nextgen', 'node-98') # added
        api.network_create('hammernet', 'anvil-nextgen')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.node_detach_network('node-98', '99-eth0') # changed
        releaseDB(db)

    def test_node_detach_network_wrong_node_not_in_project(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register('node-98') # added
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.network_create('hammernet', 'anvil-nextgen')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.node_detach_network('node-98', '99-eth0') # changed
        releaseDB(db)

    def test_node_detach_network_no_such_node(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.network_create('hammernet', 'anvil-nextgen')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.node_detach_network('node-98', '99-eth0') # changed
        releaseDB(db)

    def test_node_detach_network_no_such_nic(self):
        db = newDB()
        api.node_register('node-99')
        api.node_register_nic('node-99', '99-eth0', 'DE:AD:BE:EF:20:14')
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_connect_node('anvil-nextgen', 'node-99')
        api.network_create('hammernet', 'anvil-nextgen')
        api.node_connect_network('node-99', '99-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.node_detach_network('node-99', '99-eth1') # changed
        releaseDB(db)

class TestHeadnodeCreateDelete:

    def test_headnode_create_success(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        hn = api._must_find(db, model.Headnode, 'hn-0')
        assert hn.project.label == 'anvil-nextgen'
        releaseDB(db)

    def test_headnode_create_badproject(self):
        """Tests that creating a headnode with a nonexistent group fails"""
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.headnode_create('hn-0', 'anvil-nextgen')
        releaseDB(db)

    def test_headnode_create_duplicate(self):
        """Tests that creating a headnode with a duplicate name fails"""
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_create('anvil-oldtimer', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        with pytest.raises(api.DuplicateError):
            api.headnode_create('hn-0', 'anvil-oldtimer')
        releaseDB(db)

    def test_headnode_create_second(self):
        """Tests that creating a second headnode one one project fails"""
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        with pytest.raises(api.DuplicateError):
            api.headnode_create('hn-1', 'anvil-nextgen')
        releaseDB(db)


    def test_headnode_delete_success(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_delete('hn-0')
        api._assert_absent(db, model.Headnode, 'hn-0')
        releaseDB(db)

    def test_headnode_delete_nonexistent(self):
        """Tests that deleting a nonexistent headnode fails"""
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.headnode_delete('hn-0')
        releaseDB(db)


class TestHeadnodeCreateDeleteHnic:

    def test_headnode_create_hnic_success(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        nic = api._must_find(db, model.Hnic, 'hn-0-eth0')
        assert nic.headnode.label == 'hn-0'
        releaseDB(db)

    def test_headnode_create_hnic_no_headnode(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        releaseDB(db)

    def test_headnode_create_hnic_duplicate_hnic(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.DuplicateError):
            api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:15')
        releaseDB(db)

    def test_headnode_delete_hnic_success(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        api.headnode_delete_hnic('hn-0', 'hn-0-eth0')
        api._assert_absent(db, model.Hnic, 'hn-0-eth0')
        hn = api._must_find(db, model.Headnode, 'hn-0')
        releaseDB(db)

    def test_headnode_delete_hnic_hnic_nexist(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        with pytest.raises(api.NotFoundError):
            api.headnode_delete_hnic('hn-0', 'hn-0-eth0')
        releaseDB(db)

    def test_headnode_delete_hnic_headnode_nexist(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.headnode_delete_hnic('hn-0', 'hn-0-eth0')
        releaseDB(db)

    def test_headnode_delete_hnic_wrong_headnode(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_create('anvil-oldtimer', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create('hn-1', 'anvil-oldtimer')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.headnode_delete_hnic('hn-1', 'hn-0-eth0')
        releaseDB(db)

    def test_headnode_delete_hnic_wrong_nexist_headnode(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.headnode_delete_hnic('hn-1', 'hn-0-eth0')
        releaseDB(db)


class TestHeadnodeConnectDetachNetwork:

    def test_headnode_connect_network_success(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        api.network_create('hammernet', 'anvil-nextgen')

        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')
        network = api._must_find(db, model.Network, 'hammernet')
        hnic = api._must_find(db, model.Hnic, 'hn-0-eth0')
        assert hnic.network is network
        assert hnic in network.hnics
        releaseDB(db)

    def test_headnode_connect_network_no_such_headnode(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        api.network_create('hammernet', 'anvil-nextgen')

        with pytest.raises(api.NotFoundError):
            api.headnode_connect_network('hn-1', 'hn-0-eth0', 'hammernet') # changed
        releaseDB(db)

    def test_headnode_connect_network_no_such_hnic(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        api.network_create('hammernet', 'anvil-nextgen')

        with pytest.raises(api.NotFoundError):
            api.headnode_connect_network('hn-0', 'hn-0-eth1', 'hammernet') # changed
        releaseDB(db)

    def test_headnode_connect_network_no_such_network(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        api.network_create('hammernet', 'anvil-nextgen')

        with pytest.raises(api.NotFoundError):
            api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet2') # changed
        releaseDB(db)

    def test_headnode_connect_network_already_attached_to_same(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        api.network_create('hammernet', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet') # added

        with pytest.raises(api.DuplicateError):
            api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')
        releaseDB(db)

    def test_headnode_connect_network_already_attached_differently(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        api.network_create('hammernet', 'anvil-nextgen')
        api.network_create('hammernet2', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet') # added

        with pytest.raises(api.DuplicateError):
            api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet2') # changed
        releaseDB(db)


    def test_headnode_detach_network_success(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        api.network_create('hammernet', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

        api.headnode_detach_network('hn-0', 'hn-0-eth0')
        network = api._must_find(db, model.Network, 'hammernet')
        hnic = api._must_find(db, model.Hnic, 'hn-0-eth0')
        assert hnic.network is None
        assert hnic not in network.hnics
        releaseDB(db)

    def test_headnode_detach_network_not_attached(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        api.network_create('hammernet', 'anvil-nextgen')
#        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.headnode_detach_network('hn-0', 'hn-0-eth0')
        releaseDB(db)

    def test_headnode_detach_network_no_such_headnode(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        api.network_create('hammernet', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.headnode_detach_network('hn-1', 'hn-0-eth0') # changed
        releaseDB(db)

    def test_headnode_detach_network_no_such_hnic(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.headnode_create('hn-0', 'anvil-nextgen')
        api.headnode_create_hnic('hn-0', 'hn-0-eth0', 'DE:AD:BE:EF:20:14')
        api.network_create('hammernet', 'anvil-nextgen')
        api.headnode_connect_network('hn-0', 'hn-0-eth0', 'hammernet')

        with pytest.raises(api.NotFoundError):
            api.headnode_detach_network('hn-0', 'hn-0-eth1') # changed
        releaseDB(db)


class TestNetworkCreateDelete:
    """Tests for the haas.api.network_* functions."""

    def test_network_create_success(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.network_create('hammernet', 'anvil-nextgen')
        net = api._must_find(db, model.Network, 'hammernet')
        assert net.project.label == 'anvil-nextgen'
        releaseDB(db)

    def test_network_create_badproject(self):
        """Tests that creating a network with a nonexistent project fails"""
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.network_create('hammernet', 'anvil-nextgen')
        releaseDB(db)

    def test_network_create_duplicate(self):
        """Tests that creating a network with a duplicate name fails"""
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.project_create('anvil-oldtimer', 'acme-code')
        api.network_create('hammernet', 'anvil-nextgen')
        with pytest.raises(api.DuplicateError):
            api.network_create('hammernet', 'anvil-oldtimer')
        releaseDB(db)

    def test_network_delete_success(self):
        db = newDB()
        api.group_create('acme-code')
        api.project_create('anvil-nextgen', 'acme-code')
        api.network_create('hammernet', 'anvil-nextgen')
        api.network_delete('hammernet')
        api._assert_absent(db, model.Network, 'hammernet')
        releaseDB(db)

    def test_network_delete_nonexistent(self):
        """Tests that deleting a nonexistent network fails"""
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.network_delete('hammernet')
        releaseDB(db)

#   Tests removed for not applying in general case.  (Specific to dell switch)
#
#    def test_network_basic_vlan_leak(self):
#        db = newDB()
#        api.group_create('acme-code')
#        api.project_create('anvil-nextgen', 'acme-code')
#        api.network_create('hammernet', 'anvil-nextgen')
#        api.network_delete('hammernet')
#        # For this to work, the vlan will need to have been released:
#        api.network_create('sledge', 'anvil-nextgen')
#        releaseDB(db)
#
#    def test_network_no_duplicates(self):
#        db = newDB()
#        api.group_create('acme-code')
#        api.project_create('anvil-nextgen', 'acme-code')
#        api.network_create('hammernet', 'anvil-nextgen')
#        with pytest.raises(api.AllocationError):
#            api.network_create('sledge', 'anvil-nextgen')
#        releaseDB(db)
#

class TestSwitchRegisterDelete:
    """Tests for the haas.api.switch_* functions."""

    def test_switch_register_success(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api._must_find(db, model.Switch, 'bait-and')
        releaseDB(db)

    def test_duplicate_switch_register(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        with pytest.raises(api.DuplicateError):
            api.switch_register('bait-and', 'falling')
        releaseDB(db)

    def test_switch_delete(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.switch_delete('bait-and')
        with pytest.raises(api.NotFoundError):
            api._must_find(db, model.Switch, 'bait-and')
        releaseDB(db)

    def test_swtich_delete_nexist(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.switch_delete('bait_and')
        releaseDB(db)


class TestPortRegisterDelete:

    def test_port_register_success(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.port_register('bait-and', '3')
        releaseDB(db)

    def test_port_register_duplicate(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.port_register('bait-and', '3')
        with pytest.raises(api.DuplicateError):
            api.port_register('bait-and', '3')
        releaseDB(db)

    def test_port_register_no_such_switch(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.port_register('bait-and', '3')
        releaseDB(db)

    def test_port_delete_success(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.port_register('bait-and', '3')
        api.port_delete('bait-and', '3')
        releaseDB(db)

    def test_port_delete_no_such_port(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        with pytest.raises(api.NotFoundError):
            api.port_delete('bait-and', '3')
        releaseDB(db)

    def test_port_delete_no_such_switch(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.port_delete('bait-and', '3')
        releaseDB(db)

class TestPortConnectDetachNic:

    def test_port_connect_nic_success(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.port_register('bait-and', '3')
        api.node_register('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('bait-and', '3', 'compute-01', 'eth0')
        releaseDB(db)

    def test_port_connect_nic_no_such_switch(self):
        db = newDB()
        api.node_register('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.port_connect_nic('bait-and', '3', 'compute-01', 'eth0')
        releaseDB(db)

    def test_port_connect_nic_no_such_port(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.node_register('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.port_connect_nic('bait-and', '3', 'compute-01', 'eth0')
        releaseDB(db)

    def test_port_connect_nic_no_such_node(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.port_register('bait-and', '3')
        with pytest.raises(api.NotFoundError):
            api.port_connect_nic('bait-and', '3', 'compute-01', 'eth0')
        releaseDB(db)

    def test_port_connect_nic_no_such_nic(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.port_register('bait-and', '3')
        api.node_register('compute-01')
        with pytest.raises(api.NotFoundError):
            api.port_connect_nic('bait-and', '3', 'compute-01', 'eth0')
        releaseDB(db)

    def test_port_connect_nic_already_attached_to_same(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.port_register('bait-and', '3')
        api.node_register('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('bait-and', '3', 'compute-01', 'eth0')
        with pytest.raises(api.DuplicateError):
            api.port_connect_nic('bait-and', '3', 'compute-01', 'eth0')
        releaseDB(db)

    def test_port_connect_nic_nic_already_attached_differently(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.switch_register('-eroo', 'big-iron')
        api.port_register('bait-and', '3')
        api.port_register('-eroo', '4')
        api.node_register('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('bait-and', '3', 'compute-01', 'eth0')
        with pytest.raises(api.DuplicateError):
            api.port_connect_nic('-eroo', '4', 'compute-01', 'eth0')
        releaseDB(db)

    def test_port_connect_nic_port_already_attached_differently(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.port_register('bait-and', '3')
        api.node_register('compute-01')
        api.node_register('compute-02')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.node_register_nic('compute-02', 'eth1', 'DE:AD:BE:EF:20:15')
        api.port_connect_nic('bait-and', '3', 'compute-01', 'eth0')
        with pytest.raises(api.DuplicateError):
            api.port_connect_nic('bait-and', '3', 'compute-02', 'eth1')
        releaseDB(db)


    def test_port_detach_nic_success(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.port_register('bait-and', '3')
        api.node_register('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        api.port_connect_nic('bait-and', '3', 'compute-01', 'eth0')
        api.port_detach_nic('bait-and', '3')
        releaseDB(db)

    def test_port_detach_nic_no_such_switch(self):
        db = newDB()
        with pytest.raises(api.NotFoundError):
            api.port_detach_nic('bait-and', '3')
        releaseDB(db)

    def test_port_detach_nic_no_such_port(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        with pytest.raises(api.NotFoundError):
            api.port_detach_nic('bait-and', '3')
        releaseDB(db)

    def test_port_detach_nic_not_attached(self):
        db = newDB()
        api.switch_register('bait-and', 'big-iron')
        api.port_register('bait-and', '3')
        api.node_register('compute-01')
        api.node_register_nic('compute-01', 'eth0', 'DE:AD:BE:EF:20:14')
        with pytest.raises(api.NotFoundError):
            api.port_detach_nic('bait-and', '3')
        releaseDB(db)

