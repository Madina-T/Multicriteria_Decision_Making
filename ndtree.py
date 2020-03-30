import numpy as np
import math

class NDTree:

    def __init__(self, nb_max_points, nb_children):
        self.root = None
        self.nb_max_points = nb_max_points
        self.nb_children = nb_children

    def add(self, y):
        """
        Fonction permettant d'ajouter un point y au ND Tree
        """
        n = self.root
        if not n:
            n = Node(self.nb_max_points,self.nb_children)
            n.insert(y)
        else:
            n, update = n.update_node(y)
            if update:
                n.insert(y)
        self.root = n

    def get_points(self):
        """
        Fonction permettant de récupérer tous les points stockés dans le ND Tree
        """
        if self.root: 
            points = self.root.get_all_points()
        return points

class Node:

    def __init__(self,  nb_max_points, nb_children, parent=None):
        self.rectangle = None # rectangle = [point nadir local, point idéal local]
        self.parent = parent # père du noeud courant
        self.nodes = [] # liste des descendants du noeud courant
        self.L = [] # liste des points stockés dans le noeud courant
        self.nb_max_points = nb_max_points # nombre maximum de points que peut contenir un noeud
        self.nb_children = nb_children

        if parent:
            parent.add_node(self)

    def add_node(self, node, pos=-1):
        """
        Fonction permettant d'ajouter un noeud node à l'arbre ou de le mettre à jour 
        """
        if node not in self.nodes:
            node.parent = self
            if pos >= 0 and pos < len(self.nodes):
                self.nodes.insert(pos, node)
            else:
                self.nodes.append(node)

    def remove_node(self, node):
        """
        Fonction permettant de retirer un noeud de l'arbre
        """
        if node in self.nodes:
            self.nodes.remove(node)
            del node

    def replace_node(self, node, r_node):
        """
        Fonction permettant de remplacer un noeud node par un noeud r_node dans l'arbre courant
        """
        if node in self.nodes:
            self.add_node(r_node, self.nodes.index(node))
            self.remove_node(node)

    def add_point(self, y, pos=-1):
        """
        Fonction permettant d'ajouter un point y dans l'arbre
        """
        if pos >= 0 and pos < len(self.L):
            self.L.insert(pos, y)
        else:
            self.L.append(y)

    def remove_point(self, y):
        """
        Fonction permettant de retirer le point y de l'arbre
        """
        if y in self.L:
            self.L.remove(y)

    def get_all_points(self):
        """
        Fonction permettant de récupérer les points du noeud et de ses descendants
        """
        if self.nodes == 0: # feuille
            return self.L
        else:
            points = self.L
            for n in self.nodes:
                for p in n.get_all_points():
                    if p not in points:
                        points.append(p)
            return points


    def distance_to_middle(self, y):
        """
        Fonction permettant de calculer la distance euclidienne entre y et le segment reliant
        le point nadir au point idéal
        """
        dec = tuple(yi / 2.0 for yi in tuple(yi[0] - yi[1] for yi in zip(self.rectangle[1], self.rectangle[0])))
        middle_point = tuple(yi[0] + yi[1] for yi in zip(self.rectangle[0], dec))
        euclidean_dist = euclidian_distance(y, middle_point)
        return euclidean_dist

    def farthest_point(self):
        """
        Fonction permettant de déterminer le point le plus éloigné ( en moyenne )
        de tous les points stockés dans le noeud courant ( barycentre )
        """
        d = len(self.L[0]) if len(self.L) > 0 else 1
        y = (0,) * d
        mean_max_distance = 0
        for yp in self.L:
            l_dist = [euclidian_distance(yp, xp) for xp in self.L]
            max_distance = sum(l_dist)
            tmp_mean_max_distance = max_distance / (len(self.L) - 1)
            if tmp_mean_max_distance > mean_max_distance:
                mean_max_distance = tmp_mean_max_distance
                y = yp
        return y

    def split(self):
        """
        Fonction permettant de créer les nouveaux fils du noeud courant lorsqu'il atteint
        le nombre maximum de points pouvant être stockés en lui
        """
        y = self.farthest_point()
        new_child = Node(self.nb_max_points,self.nb_children,self)
        new_child.add_point(y)
        new_child.update_ideal_nadir(y)
        self.remove_point(y)
        while len(self.nodes) < self.nb_children:
            y = self.farthest_point()
            new_child = Node(self.nb_max_points,self.nb_children,self)
            new_child.add_point(y)
            new_child.update_ideal_nadir(y)
            self.remove_point(y)
        while self and len(self.L) > 0:
            y = self.L[0]
            new_child = sorted(self.nodes, key=lambda node: node.distance_to_middle(y))[0] # noeud le plus proche de y
            new_child.add_point(y)
            new_child.update_ideal_nadir(y)
            self.remove_point(y)

    def insert(self, y):
        """
        Fonction permettant d'insérer un point y dans l'arbre
        """
        if len(self.nodes) == 0: # leaf node
            self.add_point(y)
            self.update_ideal_nadir(y)
            if len(self.L) > self.nb_max_points:
                self.split()
        else:
            nearest_node = sorted(self.nodes, key=lambda node: node.distance_to_middle(y))[0] # noeud le plus proche de y
            nearest_node.insert(y)


    def update_node(self, y):
        """
        Fonction permettant d'insérer un point y dans l'arbre et de supprimer de l'arbre
        tous les points dominés par y
        """
        nout = self
        nadir = self.rectangle[0]
        ideal = self.rectangle[1]
        # print("On veut ajouter",y,"à",self.L)
        # print("Ideal",ideal)
        # print("Nadir",nadir)
        if all(yi[0] >= yi[1] for yi in zip(nadir, y)): # si nadir local >= y, y est rejeté
            #print("rejeté, dominé par le point nadir :",nadir)
            return nout, False
        elif all(yi[0] >= yi[1] for yi in zip(y, ideal)): # si y >= ideal local, le noeud courant et tout son sous-arbre sont suppirmés
            #print("On supprime le noeud courant et tous ses descendants")
            nparent = self.parent
            if nparent:
                nparent.remove_node(self)
            nout = Node(self.nb_max_points,self.nb_children)
        elif all(yi[0] >= yi[1] for yi in zip(ideal, y)) or all(yi[0] >= yi[1] for yi in zip(y, nadir)):
            if len(self.nodes) == 0: # si le noeud courant est une feuille
                to_remove = []
                for z in self.L: # on regarde si y domine ou est dominé par un point de la feuille
                    if all(yi[0] >= yi[1] for yi in zip(z, y)):
                        #print("rejeté, dominé par :",z)
                        return nout, False # y est rejeté
                    elif all(yi[0] > yi[1] for yi in zip(y, z)):
                        to_remove.append(z)
                for z in to_remove:
                    #print(z,"est retiré de l'arbre")
                    self.remove_point(z) # z est retiré de l'arbre
            else:
                to_remove = []
                for child in self.nodes:
                    child, update = child.update_node(y)
                    if not update:
                        return nout, False # y n'a pu être inséré dans aucun noeud
                    elif not child or (len(child.L) == 0 and len(child.nodes) == 0): # noeud vide
                        to_remove.append(child)
                for child in to_remove:
                    self.remove_node(child)
                if len(self.nodes) == 1: # si le noeud courant n'a plus qu'un seul enfant
                    child = self.nodes[0]
                    #print(self.L,"\nremplacé par\n",child.L)
                    nparent = self.parent
                    if nparent:
                        nparent.replace_node(self, child) # on le remplace par celui-ci
        return nout, True

    def update_ideal_nadir(self, y):
        """
        Fonction permettant de mettre à jour le point nadir local et le point ideal local
        selon la valeur de y
        """
        if not self.rectangle:
            n = len(y)
            nadir = (np.inf,) * n
            ideal = (-np.inf,) * n
            self.rectangle =  [nadir, ideal]
        else:
            nadir = self.rectangle[0] # approximation du point nadir pour le noeud courant
            ideal = self.rectangle[1] # approximation du point idéal pour le noeud courant

        updateIdeal = any(yi > ideali for yi, ideali in zip(y, ideal))
        updateNadir = any(yi < nadiri for yi, nadiri in zip(y, nadir))

        if updateIdeal or updateNadir:
            nadir = tuple(min(yi, nadiri) for yi, nadiri in zip(y, nadir))
            ideal = tuple(max(yi, ideali) for yi, ideali in zip(y, ideal))
            self.rectangle[0] = nadir
            self.rectangle[1] = ideal
            if self.parent:
                nparent = self.parent
                nparent.update_ideal_nadir(y)

def euclidian_distance(y1, y2):
    """
    Fonction permettant de calculer la distance euclidienne entre les points y1 et y2
    """
    sq = tuple(yi * yi for yi in tuple(yi[0] - yi[1] for yi in zip(y1, y2)))
    s = sum(sq)
    return math.sqrt(s)
