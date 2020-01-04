"""Site structure tests"""
import pytest

from scrapy_patterns.site_structure import SiteStructure, VisitState


def test_create_site_structure():
    """Tests the creation of a site structure."""
    structure = SiteStructure("root_name")
    assert structure.root_node is not None
    assert structure.root_node.name == "(root) root_name"


def test_add_node_with_path():
    """Tests adding a node with path"""
    structure = SiteStructure("root_name")
    node_animals = structure.add_node_with_path("/animals", "animals_url")
    assert node_animals is not None
    assert structure.get_node_at_path("animals") is not None, "animals doesn't exist!"
    node_fish = structure.add_node_with_path("animals/fish", "fish_urls")
    assert node_fish is not None
    assert structure.get_node_at_path("/animals/fish") is not None, "/animals/fish doesn't exist!"


def test_add_node_ancestors_do_not_exist():
    """Tests trying to add a node with path where ancestors don't exist."""
    structure = __create_test_structure()
    with pytest.raises(RuntimeError):
        structure.add_node_with_path("/animals/worm/earthworm", "worm_url")


def test_to_dict():
    """Tests converting a structure to a dict"""
    structure = __create_test_structure()
    structure_dict = structure.to_dict()
    assert structure_dict["name"] == "(root) root_name", "Name of root node in dict is wrong!"
    assert structure_dict["children"][0]["name"] == "animals", "Name of root's child is wrong!"


def test_from_dict():
    """Tests converting a dict to a site structure"""
    structure = __create_test_structure()
    structure_dict = structure.to_dict()
    converted_structure = SiteStructure.from_dict(structure_dict)
    root_node = converted_structure.root_node
    assert root_node.name == "(root) root_name"
    node_animals = converted_structure.root_node.children[0]
    assert node_animals.name == "animals"
    node_fish = structure.get_node_at_path("/animals/fish")
    assert node_fish is not None


def test_set_visit_state():
    """Tests setting the visit state of a node"""
    structure = __create_test_structure()
    node_salmon = structure.get_node_at_path("animals/fish/salmon")
    node_salmon.set_visit_state(VisitState.IN_PROGRESS)
    assert node_salmon.visit_state == VisitState.IN_PROGRESS, "Failed to set visit state!"


def test_set_visit_state_propagate():
    """Tests setting the visit state of a node"""
    structure = __create_test_structure()
    node_salmon = structure.get_node_at_path("animals/fish/salmon")
    node_salmon.set_visit_state(VisitState.IN_PROGRESS, True)
    node = node_salmon
    while node is not None:
        assert node.visit_state == VisitState.IN_PROGRESS, "Failed to propagate visit state!"
        node = node.parent


def test_find_leaf_with_visit_state():
    """Tests finding a leaf node with a single visit state"""
    structure = __create_test_structure()
    node_salmon = structure.get_node_at_path("animals/fish/salmon")
    node_salmon.set_visit_state(VisitState.IN_PROGRESS)
    node_insect = structure.get_node_at_path("animals/insect")
    node_insect.visit_state = VisitState.IN_PROGRESS
    searched_node = structure.find_leaf_with_visit_state(VisitState.IN_PROGRESS)
    assert searched_node is not None, "Failed to find node with 'IN_PROGRESS' state!"
    assert searched_node.name == "salmon", "Found node should be 'salmon'"


def test_find_leaf_with_visit_states_list():
    """Tests finding a leaf node with a visit state list"""
    structure = __create_test_structure()
    node_salmon = structure.get_node_at_path("animals/fish/salmon")
    node_salmon.set_visit_state(VisitState.IN_PROGRESS)
    node_insect = structure.get_node_at_path("animals/insect")
    node_insect.visit_state = VisitState.IN_PROGRESS
    searched_node = structure.find_leaf_with_visit_state([VisitState.VISITED, VisitState.IN_PROGRESS])
    assert searched_node is not None, "Failed to find node with 'IN_PROGRESS' state!"
    assert searched_node.name == "salmon", "Found node should be 'salmon'"


def test_to_string():
    """Tests that to string works as expected"""
    structure = __create_test_structure()
    structure_str = str(structure)
    expected_str = "" \
                   "(root) root_name\n" \
                   "├── [NEW] animals (animals_url)\n" \
                   "|   ├── [NEW] fish (fish_url)\n" \
                   "|   |   └── [NEW] salmon (salmon_url)\n" \
                   "|   └── [NEW] insect (insect_url)\n" \
                   "└── [NEW] plants (plant_url)\n" \
                   "    └── [NEW] carrot (carrot_url)"
    assert expected_str == structure_str


def test_get_path():
    """Tests getting the path of a node"""
    structure = __create_test_structure()
    node_salmon = structure.get_node_at_path("/animals/fish/salmon")
    path_salmon = node_salmon.get_path()
    assert path_salmon == "/animals/fish/salmon"


def test_find_leaf_not_found():
    """Tests finding a leaf with no match"""
    structure = __create_test_structure()
    search_node = structure.find_leaf_with_visit_state(VisitState.VISITED)
    assert search_node is None, "Found an unexpected node!"


def test_find_leaf_visit_state_none():
    """Tests that exception is raised when visit_state is None"""
    structure = __create_test_structure()
    with pytest.raises(TypeError):
        structure.find_leaf_with_visit_state(None)


def test_find_leaf_visit_states_empty():
    """Tests that exception is raised when visit_state is an empty list."""
    structure = __create_test_structure()
    with pytest.raises(ValueError):
        structure.find_leaf_with_visit_state([])


def test_add_duplicate():
    """Tests that adding duplicate node fails."""
    structure = SiteStructure("root_name")
    structure.add_node_with_path("animals", "animals_url")
    with pytest.raises(RuntimeError):
        structure.add_node_with_path("animals", "animals_url")


def __create_test_structure():
    structure = SiteStructure("root_name")
    structure.add_node_with_path("animals", "animals_url")
    structure.add_node_with_path("animals/fish", "fish_url")
    structure.add_node_with_path("animals/fish/salmon", "salmon_url")
    structure.add_node_with_path("animals/insect", "insect_url")
    structure.add_node_with_path("plants", "plant_url")
    structure.add_node_with_path("plants/carrot", "carrot_url")
    return structure
