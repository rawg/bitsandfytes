package hack.instances

package object bitSet extends BitSetInstances

import hack.classes.Semigroup

import scala.collection.BitSet

trait BitSetInstances {
  implicit val semigroupBitSet: Semigroup[BitSet] =
    new SemigroupBitSet
}

class SemigroupBitSet extends Semigroup[BitSet] {
  override def op(a: BitSet, b: BitSet): BitSet = a | b
}