"""Contains classes that are used to describe the structure of a site."""
from enum import Enum
from typing import Optional, List, Union


class VisitState(Enum):
    """Visit state of a category (node)"""
    NEW = 0
    IN_PROGRESS = 1
    VISITED = 2


class Node:
    """
    The node (category). Most sites are built around categories, which in turn can contain sub-categories, etc...
    Therefore the structure of a site is represented as a tree.
    Attributes:
        name (str): The name of the node.
        url (str): The url at which the node (category) is available.
        parent (Node): The parent of the node.
        visit_state (VisitState): The visit state of the node. Default value is VisitState.NEW
        children (List[Node]): Children of node. Default value is an empty list.
    """

    def __init__(self, name: str, url: str, parent: 'Node' = None):
        """
        Args:
            name: The name of the node
            url: The url at which the node (category) is available.
            parent: The node's parent.
        """
        self.name = name
        self.url = url
        self.visit_state = VisitState.NEW
        self.children: List[Node] = []
        self.parent: Node = parent

    def get_path(self) -> str:
        """
        Returns: The path of the node separated by slashes (/), excluding the name of the root node. Paths consists of
        the names of the nodes.
        """
        if self.parent is None:
            return ""
        else:
            return self.parent.get_path() + "/" + self.name

    def to_dict(self):
        """
        Returns: A dict representation of the tree rooted at this node.
        """
        node_dict = {"name": self.name, "url": self.url, "visit_state": self.visit_state.name, "children": []}
        if self.children:
            children = [node.to_dict() for node in self.children]
            node_dict.update({"children": children})
        return node_dict

    @classmethod
    def from_dict(cls, node_dict: dict):
        """
        Construct a tree from its dict representation.
        Args:
            node_dict: The dict representation.

        Returns: The restored tree.
        """
        name = node_dict["name"]
        url = node_dict["url"]
        visit_state = VisitState[node_dict["visit_state"]]
        node = Node(name, url)
        node.visit_state = visit_state
        if node_dict["children"]:
            for child_dict in node_dict["children"]:
                child_node = Node.from_dict(child_dict)
                child_node.parent = node
                node.children.append(child_node)
        return node

    def set_visit_state(self, visit_state: VisitState, propagate: bool = False):
        """
        Sets the visit state of this node optionally propagating it to ancestors.
        Args:
            visit_state: The new state.
            propagate: Whether to propagate to ancestors.
        """
        self.visit_state = visit_state
        if self.parent and propagate:
            self.parent.set_visit_state(visit_state, propagate)


class SiteStructure:
    """
    Handles the nodes of the structure.
    Attributes:
        root_node (Node): The root node.
    """

    def __init__(self, name=""):
        """
        Creates the structure with a root node initialized to the given name prefixed with '(root) '.
        Args:
            name: The name of the root node. (The root node doesn't have an url)
        """
        self.root_node = Node("(root) %s" % name, "")

    def add_node_with_path(self, path: str, url: str):
        """
        Adds a new node with url under path, where the name of the new node will be the last part of the path.
        Nodes along the path should pre-exists except for the last node.
        Args:
            path (str): The path.
            url (str): The url.

        Returns: The newly created node.
        """
        if self.get_node_at_path(path) is not None:
            raise RuntimeError("Path \"%s\" already exists!" % path)
        used_path = path.strip("/")
        node_names = self.__split_path(used_path)
        children = self.root_node.children
        parent = self.root_node
        if len(node_names) > 1:
            parent_path = "/".join(node_names[:-1])
            existing = self.get_node_at_path(parent_path)
            if existing:
                parent = existing
                children = existing.children
            else:
                raise RuntimeError("Parent path \"%s\" not existing!" % parent_path)
        new_node_name = node_names[-1]
        node = Node(new_node_name, url, parent)
        children.append(node)
        return node

    def get_node_at_path(self, path: str) -> Node:
        """
        Gets a node at path.
        Args:
            path (str): The path

        Returns: The node if found, else None.
        """
        children = self.root_node.children
        result_node = None
        used_path = path.strip("/")
        for node_name in self.__split_path(used_path):
            result_node = self.__find_node(node_name, children)
            if result_node is None:
                break
            children = result_node.children
        return result_node

    def to_dict(self):
        """
        Returns: The structure as a dict.
        """
        return self.root_node.to_dict()

    @classmethod
    def from_dict(cls, struct_dict):
        """
        Creates a structure from its dict representation.
        Args:
            struct_dict: The dict.

        Returns: The site structure.
        """
        structure = SiteStructure()
        structure.root_node = Node.from_dict(struct_dict)
        return structure

    def find_leaf_with_visit_state(self, visit_state: Union[VisitState, List[VisitState]]) -> Optional[Node]:
        """
        Finds a leaf node with matching visit state(s). Search is DFS.
        Args:
            visit_state: Either a VisitState, or list of VisitStates. If a list, a match is found when any of the
            list's element matches.

        Returns: The first matching node if found, else None.

        """
        if visit_state is None:
            raise TypeError("Visit state cannot be none")
        if isinstance(visit_state, list) and not visit_state:
            raise ValueError("Visit states is empty!")
        return self.__find_leaf_with_visit_state(visit_state, self.root_node)

    def __str__(self):
        return "\n".join(self.__create_log_msg_records(self.root_node))

    def __find_leaf_with_visit_state(self, visit_state: Union[VisitState, List[VisitState]], node: Node):
        is_leaf = len(node.children) == 0
        if is_leaf and self.__visit_state_matches(visit_state, node):
            return node
        for child in node.children:
            descendant_match = self.__find_leaf_with_visit_state(visit_state, child)
            if descendant_match:
                return descendant_match
        return None

    @staticmethod
    def __visit_state_matches(visit_state, node):
        if isinstance(visit_state, list):
            return node.visit_state in visit_state
        else:
            return node.visit_state == visit_state

    @staticmethod
    def __find_node(name, nodes):
        for node in nodes:
            if node.name == name:
                return node
        return None

    @staticmethod
    def __split_path(path):
        return path.split("/")

    def __create_log_msg_records(self, node: Node, prefix=""):
        records = []
        is_root = node.parent is None
        has_sibling = self.__has_sibling(node)
        node_prefix = self.__create_node_prefix(is_root, has_sibling)
        node_prefix = prefix + node_prefix
        log_msg_record = self.__create_single_log_msg_record(node, node_prefix)
        records.append(log_msg_record)
        carry_on_prefix = self.__create_carry_on_prefix(is_root, has_sibling)
        carry_on_prefix = prefix + carry_on_prefix
        for child in node.children:
            records.extend(self.__create_log_msg_records(child, carry_on_prefix))
        return records

    @staticmethod
    def __create_single_log_msg_record(node, node_prefix):
        is_root = node.parent is None
        if is_root:
            return node.name
        else:
            return "%s[%s] %s (%s)" % (node_prefix, node.visit_state.name, node.name, node.url)

    @staticmethod
    def __has_sibling(child):
        if child and child.parent:
            return child.parent.children[-1].name != child.name
        return None

    @staticmethod
    def __create_node_prefix(is_root, has_sibling):
        if is_root:
            return ""
        if has_sibling:
            return "├── "
        else:
            return "└── "

    @staticmethod
    def __create_carry_on_prefix(is_root, has_sibling):
        if is_root:
            return ""
        if has_sibling:
            return "|   "
        else:
            return "    "
