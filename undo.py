import globals_

class UndoStack:
    """
    A stack you can push UndoActions on, and stuff.
    """

    def __init__(self):
        self.pastActions = []
        self.futureActions = []

    def addAction(self, act):
        """
        Adds an action to the stack
        """
        self.pastActions.append(act)
        self.futureActions = []

        self.enableOrDisableMenuItems()

    def addOrExtendAction(self, act):
        """
        Adds an action to the stack, or extends the current one if applicable
        """
        if len(self.pastActions) > 0 and self.pastActions[-1].isExtentionOf(act):
            self.pastActions[-1].extend(act)
            self.enableOrDisableMenuItems()
        else:
            self.addAction(act)

    def undo(self):
        """
        Undoes the last action
        """
        if len(self.pastActions) == 0: return

        act = self.pastActions.pop()
        while act.isNull():
            # Keep popping null actions off
            if len(self.pastActions) == 0:
                return
            act = self.pastActions.pop()

        act.undo()
        self.futureActions.append(act)

        self.enableOrDisableMenuItems()

    def redo(self):
        """
        Redoes the last undone action
        """
        if len(self.futureActions) == 0: return

        act = self.futureActions.pop()
        while act.isNull():
            # Keep popping null actions off
            act = self.futureActions.pop()

        act.redo()
        self.pastActions.append(act)

        self.enableOrDisableMenuItems()

    def enableOrDisableMenuItems(self):
        """
        Enables or disables the menu items of mainWindow
        """
        globals_.mainWindow.actions['undo'].setEnabled(len(self.pastActions) > 0)
        globals_.mainWindow.actions['redo'].setEnabled(len(self.futureActions) > 0)


class UndoAction:
    """
    Abstract undo action
    """

    def undo(self):
        """
        Sets the target to its initial state
        """
        pass

    def redo(self):
        """
        Sets the target to its final state
        """
        pass

    def isExtentionOf(self, other):
        """
        Returns True if this action extends another, else False
        """
        return False

    def extend(self, other):
        """
        Extends this UndoAction with the data from an extention of it.
        isExtentionOf must have returned True first!
        """
        pass

    def isNull(self):
        """
        Returns True if this action is effectively a no-op
        """
        return True


class MoveItemUndoAction(UndoAction):
    """
    An UndoAction for movement of a single level item that is not an object
    """

    def __init__(self, target, origX, origY, finalX, finalY):
        """
        Initializes the undo action
        """
        defType = target.instanceDef
        self.origDef = defType(target)
        self.finalDef = defType(target)
        self.origDef.objx = origX
        self.origDef.objy = origY
        self.finalDef.objx = finalX
        self.finalDef.objy = finalY

    def undo(self):
        """
        Sets the target object's position to the original position
        """
        instance = self.finalDef.findInstance()
        if instance:
            self.changeObjectPos(instance, self.origDef.objx, self.origDef.objy)
        else:
            print('Undo Move Item: Cannot find item instance! ' + str(self.finalDef))

    def redo(self):
        """
        Sets the target object's position to the final position
        """
        instance = self.origDef.findInstance()
        if instance:
            self.changeObjectPos(instance, self.finalDef.objx, self.finalDef.objy)
        else:
            print('Redo Move Item: Cannot find item instance! ' + str(self.origDef))

    @staticmethod
    def changeObjectPos(object, newX, newY):
        """
        Changes the position of an object
        """
        # This causes a circular import
        return
        # oldBR = object.getFullRect()

        # if isinstance(object, SpriteItem):
        #     # Sprites are weird so they handle this themselves
        #     object.setNewObjPos(newX, newY)
        # elif isinstance(object, ObjectItem):
        #     # Objects use the objx and objy properties differently
        #     object.objx, object.objy = newX, newY
        #     object.setPos(newX * 24, newY * 24)
        # else:
        #     # Everything else is normal
        #     object.objx, object.objy = newX, newY
        #     object.setPos(newX * 1.5, newY * 1.5)
        # newBR = object.getFullRect()

        # globals_.mainWindow.scene.update(oldBR)
        # globals_.mainWindow.scene.update(newBR)

        # if isinstance(object, PathItem):
        #     object.updatePos()
        #     object.pathinfo['peline'].nodePosChanged()

    def isExtentionOf(self, other):
        """
        Returns True if this MoveItemUndoAction extends another
        """
        return hasattr(other, 'origDef') and self.origDef.defMatchesData(other.origDef)

    def extend(self, other):
        """
        Extends this MoveItemUndoAction with the data from an extention of it.
        isExtentionOf must have returned True first!
        """
        self.finalDef.objx = other.finalDef.objx
        self.finalDef.objy = other.finalDef.objy

    def isNull(self):
        """
        Returns True if this action is effectively a no-op
        """
        matches = True
        matches = matches and abs(self.origDef.objx - self.finalDef.objx) <= 2
        matches = matches and abs(self.origDef.objy - self.finalDef.objy) <= 2
        return matches


class SimultaneousUndoAction(UndoAction):
    """
    An undo action that consists of multiple undo actions at once
    """

    def __init__(self, children):
        """
        Initializes the undo action
        """
        self.children = set(children)

    def undo(self):
        """
        Calls undo() on all children
        """
        for c in self.children:
            c.undo()

    def redo(self):
        """
        Calls redo() on all children
        """
        for c in self.children:
            c.redo()

    def isExtentionOf(self, other):
        """
        Returns True if this SinultaneousUndoAction and another one have equivalent children
        """
        if not hasattr(other, 'children'): return False
        searchIn = set(self.children)
        searchAgainst = set(other.children)
        for searchInObj in searchIn:
            found = False
            for searchAgainstObj in searchAgainst:
                if searchAgainstObj.isExtentionOf(searchInObj):
                    found = True
                    searchAgainst.remove(searchAgainstObj)
                    break  # only breaks out of inner loop
            if not found:
                return False
        return True

    def extend(self, other):
        """
        Extend this SimultaneousUndoAction with the data from an extention of it.
        isExtentionOf must have returned True first!
        """
        searchMine = set(self.children)
        searchOther = set(other.children)
        for searchMineObj in searchMine:
            for searchOtherObj in searchOther:
                if searchOtherObj.isExtentionOf(searchMineObj):
                    searchMineObj.extend(searchOtherObj)
                    searchOther.remove(searchOtherObj)
                    break  # only breaks out of inner loop

    def isNull(self):
        """
        Returns True if this action is effectively a no-op
        """
        # Hopefully this code is easy enough for you to follow.
        anythingIsDifferent = False
        for c in self.children:
            anythingIsDifferent = anythingIsDifferent or not c.isNull()
        return not anythingIsDifferent
