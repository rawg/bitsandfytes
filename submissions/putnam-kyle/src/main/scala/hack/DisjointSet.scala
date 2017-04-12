package hack

import classes.Semigroup

import scala.annotation.tailrec
import scala.reflect.ClassTag

object DisjointSet {

  import instances.unit._

  def fromSize(n: Int): DisjointSet[Int, Unit] =
    Bare(Range(0, n).toArray, Array.fill(n)(1), Array.fill(n)(Unit))

  def fromLabels[L](xs: Map[Int, L])
                   (implicit m: Semigroup[L], t: ClassTag[L]): DisjointSet[Int, L] = {
    val maxId   = xs.keys.max + 1
    val parents = Range(0, maxId).toArray
    val sizes   = Array.fill(maxId)(1)
    val labels  = Range(0, maxId).map(n => xs.getOrElse(n, null.asInstanceOf[L])).toArray
    Bare(parents, sizes, labels)
  }

  def fromMap[E, L](xs: Map[E, L])
                   (implicit m: Semigroup[L], t: ClassTag[L]): DisjointSet[E, L] = {
    val names  = xs.keys.toVector
    val labels = names.map(xs).toArray
    val index  = names.zip(Range(0, xs.size)).toMap
    val bare   = Bare(Range(0, xs.size).toArray, Array.fill(xs.size)(1), labels)
    Wrapped(bare, names, index)
  }
}

abstract sealed class DisjointSet[E, L] {
  /** Representative element for given element */
  def root(a: E): E

  /** Set of all representative elements */
  def roots: Set[E]

  /** Number of elements connected to given element */
  def size(a: E): Int

  /** Label for elements connected to given element */
  def label(a: E): L

  /** Connects two elements */
  def union(a: E, b: E): DisjointSet[E, L]

  /** Tests if two elements are connected (directly or transitively) */
  def connected(a: E, b: E): Boolean
}

case class Wrapped[E, L](bare:  Bare[L],
                         names: Vector[E],
                         index: Map[E, Int])
extends DisjointSet[E, L] {

  @Override
  def root(a: E): E =
    names(bare.root(index(a)))

  @Override
  def roots: Set[E] =
    bare.roots.map(names)

  @Override
  def label(a: E): L =
    bare.label(index(a))

  @Override
  def size(a: E): Int =
    bare.size(index(a))

  @Override
  def union(a: E, b: E): Wrapped[E, L] =
    Wrapped(bare.union(index(a), index(b)), names, index)

  @Override
  def connected(a: E, b: E): Boolean =
    bare.connected(index(a), index(b))
}

case class Bare[L](parents: Array[Int],
                   sizes:   Array[Int],
                   labels:  Array[L])
                  (implicit m: Semigroup[L], e: ClassTag[L])
extends DisjointSet[Int, L] {

  @Override
  def size(a: Int): Int =
    sizes(root(a))

  @Override
  def label(a: Int): L =
    labels(root(a))

  @Override
  def union(a: Int, b: Int): Bare[L] = {
    val rootA = root(a)
    val rootB = root(b)

    val sizeA = sizes(rootA)
    val sizeB = sizes(rootB)

    if (sizeA < sizeB)
      link(rootA, rootB, sizeA + sizeB, m.op(labels(rootA), labels(rootB)))
    else
      link(rootB, rootA, sizeA + sizeB, m.op(labels(rootB), labels(rootA)))
  }

  // link a to b, update b's size, update b's labels
  private def link(a: Int, b: Int, n: Int, l: L): Bare[L] =
    Bare(parents.updated(a, b), sizes.updated(b, n), labels.updated(b, l))

  @Override
  def connected(a: Int, b: Int): Boolean =
    root(a) == root(b)

  @Override
  def root(a: Int): Int =
    root(a, parents(a))

  @Override
  def roots: Set[Int] =
    parents.map(p => root(p, parents(p))).toSet

  @tailrec
  private def root(a: Int, p: Int): Int = {
    if (a == p) return a // self-parent
    val g = parents(p)   // grandparent of a
    parents(a) = g       // ... becomes parent of a (path-shortening optimization)
    root(p, g)
  }
}