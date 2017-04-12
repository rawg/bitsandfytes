package hack.instances

package object unit extends UnitInstances

import hack.classes.Semigroup

trait UnitInstances {
  implicit val semigroupUnit: Semigroup[Unit] =
    new SemigroupUnit
}

class SemigroupUnit extends Semigroup[Unit] {
  override def op(a: Unit, b: Unit): Unit = Unit
}