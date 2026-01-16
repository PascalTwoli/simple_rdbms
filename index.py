"""
B-tree index implementation for efficient lookups.
"""

from typing import Any, List, Optional, Tuple, Dict


class BTreeNode:
    """A node in the B-tree."""
    
    def __init__(self, leaf: bool = False):
        self.leaf = leaf
        self.keys: List[Any] = []
        self.values: List[List[int]] = []  # List of row IDs for each key
        self.children: List['BTreeNode'] = []
    
    def __repr__(self):
        return f"BTreeNode(leaf={self.leaf}, keys={self.keys})"


class BTree:
    """
    B-tree index for efficient key-based lookups.
    Supports duplicate keys (for non-unique indexes).
    """
    
    def __init__(self, order: int = 4):
        """
        Initialize a B-tree.
        
        Args:
            order: The maximum number of children per node (minimum order is 3)
        """
        self.order = max(order, 3)
        self.root = BTreeNode(leaf=True)
        self._size = 0
    
    @property
    def min_keys(self) -> int:
        """Minimum number of keys in a non-root node."""
        return (self.order - 1) // 2
    
    @property
    def max_keys(self) -> int:
        """Maximum number of keys in a node."""
        return self.order - 1
    
    def insert(self, key: Any, row_id: int) -> None:
        """
        Insert a key-value pair into the index.
        
        Args:
            key: The key to index
            row_id: The row ID associated with this key
        """
        root = self.root
        
        # If root is full, split it
        if len(root.keys) == self.max_keys:
            new_root = BTreeNode(leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
        
        self._insert_non_full(self.root, key, row_id)
        self._size += 1
    
    def _insert_non_full(self, node: BTreeNode, key: Any, row_id: int) -> None:
        """Insert into a node that is not full."""
        i = len(node.keys) - 1
        
        if node.leaf:
            # Find position for key
            while i >= 0 and self._compare(key, node.keys[i]) < 0:
                i -= 1
            
            # Check if key already exists
            if i >= 0 and self._compare(key, node.keys[i]) == 0:
                # Add row_id to existing key's list
                node.values[i].append(row_id)
            else:
                # Insert new key
                node.keys.insert(i + 1, key)
                node.values.insert(i + 1, [row_id])
        else:
            # Find child to descend into
            while i >= 0 and self._compare(key, node.keys[i]) < 0:
                i -= 1
            i += 1
            
            # Split child if full
            if len(node.children[i].keys) == self.max_keys:
                self._split_child(node, i)
                if self._compare(key, node.keys[i]) > 0:
                    i += 1
            
            self._insert_non_full(node.children[i], key, row_id)
    
    def _split_child(self, parent: BTreeNode, index: int) -> None:
        """Split a full child node."""
        order = self.order
        child = parent.children[index]
        mid = len(child.keys) // 2
        
        # Create new node for right half
        new_node = BTreeNode(leaf=child.leaf)
        
        # Move keys and values
        parent.keys.insert(index, child.keys[mid])
        parent.values.insert(index, child.values[mid])
        
        new_node.keys = child.keys[mid + 1:]
        new_node.values = child.values[mid + 1:]
        child.keys = child.keys[:mid]
        child.values = child.values[:mid]
        
        # Move children if not leaf
        if not child.leaf:
            new_node.children = child.children[mid + 1:]
            child.children = child.children[:mid + 1]
        
        parent.children.insert(index + 1, new_node)
    
    def search(self, key: Any) -> List[int]:
        """
        Search for a key and return all associated row IDs.
        
        Args:
            key: The key to search for
            
        Returns:
            List of row IDs, or empty list if key not found
        """
        return self._search(self.root, key)
    
    def _search(self, node: BTreeNode, key: Any) -> List[int]:
        """Recursively search for a key."""
        i = 0
        while i < len(node.keys) and self._compare(key, node.keys[i]) > 0:
            i += 1
        
        if i < len(node.keys) and self._compare(key, node.keys[i]) == 0:
            return list(node.values[i])  # Return a copy
        
        if node.leaf:
            return []
        
        return self._search(node.children[i], key)
    
    def delete(self, key: Any, row_id: int) -> bool:
        """
        Delete a specific key-value pair from the index.
        
        Args:
            key: The key to delete
            row_id: The specific row ID to remove
            
        Returns:
            True if the key-value pair was found and deleted
        """
        deleted = self._delete(self.root, key, row_id)
        
        # If root has no keys but has children, make first child the new root
        if len(self.root.keys) == 0 and not self.root.leaf:
            self.root = self.root.children[0]
        
        if deleted:
            self._size -= 1
        return deleted
    
    def _delete(self, node: BTreeNode, key: Any, row_id: int) -> bool:
        """Recursively delete a key-value pair."""
        i = 0
        while i < len(node.keys) and self._compare(key, node.keys[i]) > 0:
            i += 1
        
        if node.leaf:
            if i < len(node.keys) and self._compare(key, node.keys[i]) == 0:
                if row_id in node.values[i]:
                    node.values[i].remove(row_id)
                    if len(node.values[i]) == 0:
                        node.keys.pop(i)
                        node.values.pop(i)
                    return True
            return False
        else:
            if i < len(node.keys) and self._compare(key, node.keys[i]) == 0:
                # Key is in this internal node
                if row_id in node.values[i]:
                    node.values[i].remove(row_id)
                    if len(node.values[i]) == 0:
                        # Need to remove key from internal node
                        # This is a simplified version - production would need rebalancing
                        node.keys.pop(i)
                        node.values.pop(i)
                    return True
            return self._delete(node.children[i], key, row_id)
    
    def range_search(self, min_key: Any = None, max_key: Any = None) -> List[Tuple[Any, int]]:
        """
        Search for all keys in a range.
        
        Args:
            min_key: Minimum key (inclusive), None for no minimum
            max_key: Maximum key (inclusive), None for no maximum
            
        Returns:
            List of (key, row_id) tuples
        """
        results = []
        self._range_search(self.root, min_key, max_key, results)
        return results
    
    def _range_search(self, node: BTreeNode, min_key: Any, max_key: Any, 
                      results: List[Tuple[Any, int]]) -> None:
        """Recursively search for keys in a range."""
        for i, key in enumerate(node.keys):
            # Check children before this key
            if not node.leaf:
                if min_key is None or self._compare(key, min_key) >= 0:
                    self._range_search(node.children[i], min_key, max_key, results)
            
            # Check this key
            if ((min_key is None or self._compare(key, min_key) >= 0) and
                (max_key is None or self._compare(key, max_key) <= 0)):
                for row_id in node.values[i]:
                    results.append((key, row_id))
        
        # Check last child
        if not node.leaf and len(node.children) > len(node.keys):
            if max_key is None or (node.keys and self._compare(node.keys[-1], max_key) <= 0):
                self._range_search(node.children[-1], min_key, max_key, results)
    
    def _compare(self, a: Any, b: Any) -> int:
        """Compare two keys."""
        if a is None and b is None:
            return 0
        if a is None:
            return -1
        if b is None:
            return 1
        if a < b:
            return -1
        elif a > b:
            return 1
        return 0
    
    def __len__(self) -> int:
        return self._size
    
    def __contains__(self, key: Any) -> bool:
        return len(self.search(key)) > 0


class IndexManager:
    """
    Manages indexes for a table.
    """
    
    def __init__(self):
        self._indexes: Dict[str, BTree] = {}  # column_name -> BTree
    
    def create_index(self, column_name: str, order: int = 32) -> BTree:
        """Create an index on a column."""
        lower_name = column_name.lower()
        if lower_name in self._indexes:
            return self._indexes[lower_name]
        
        index = BTree(order=order)
        self._indexes[lower_name] = index
        return index
    
    def get_index(self, column_name: str) -> Optional[BTree]:
        """Get the index for a column, if it exists."""
        return self._indexes.get(column_name.lower())
    
    def has_index(self, column_name: str) -> bool:
        """Check if a column has an index."""
        return column_name.lower() in self._indexes
    
    def drop_index(self, column_name: str) -> bool:
        """Drop an index on a column."""
        lower_name = column_name.lower()
        if lower_name in self._indexes:
            del self._indexes[lower_name]
            return True
        return False
    
    def list_indexes(self) -> List[str]:
        """List all indexed columns."""
        return list(self._indexes.keys())
    
    def insert(self, column_name: str, key: Any, row_id: int) -> None:
        """Insert a key into a column's index."""
        index = self._indexes.get(column_name.lower())
        if index:
            index.insert(key, row_id)
    
    def delete(self, column_name: str, key: Any, row_id: int) -> None:
        """Delete a key from a column's index."""
        index = self._indexes.get(column_name.lower())
        if index:
            index.delete(key, row_id)
    
    def search(self, column_name: str, key: Any) -> Optional[List[int]]:
        """Search for a key in a column's index."""
        index = self._indexes.get(column_name.lower())
        if index:
            return index.search(key)
        return None
    
    def clear(self) -> None:
        """Remove all indexes."""
        self._indexes.clear()
