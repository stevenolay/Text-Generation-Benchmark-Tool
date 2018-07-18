class ListNode(object):
    def __init__(self, val, index):
        self.val = val
        self.next = None
        self.index = index


class LinkedList(object):
    def __init__(self):
        self.root = None

    def __str__(self):
        curr = self.root
        collect = []
        while curr:
            collect.append([curr.index, curr.val])
            curr = curr.next

        return str(collect)

    def insertVal(self, val, index):
        node = ListNode(val, index)
        if not self.root:
            self.root = node
        else:
            self.add(node)

    def addToList(self, node):
        curr = self.root
        while curr:
            if not curr.next:
                curr.next = node
                return
            curr = curr.next

    def add(self, listNode):
        curr = self.root
        while curr:
            if curr.val < listNode.val:
                currVal = curr.val
                currIndex = curr.index
                currNext = curr.next

                curr.val = listNode.val
                curr.index = listNode.index
                curr.next = listNode

                listNode.val = currVal
                listNode.index = currIndex
                listNode.next = currNext
                return
            if not curr.next:
                curr.next = listNode
                return
            curr = curr.next

    def topIndices(self, n):
        indices = []
        curr = self.root
        for i in range(n):
            if not curr:
                break

            index = curr.index
            indices.append(index)
            curr = curr.next

        return indices
