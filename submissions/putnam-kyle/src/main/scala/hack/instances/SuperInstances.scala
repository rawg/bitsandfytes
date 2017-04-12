package hack.instances

package object super_ extends Super_

import hack.classes.Semigroup
import hack.Super

trait Super_ {
  implicit val semigroupSupercat: Semigroup[Super] =
    new SemigroupSuper
}

class SemigroupSuper extends Semigroup[Super] {
  override def op(a: Super, b: Super): Super =
    Super(a.articles | b.articles,
      a.categories   | b.categories,
      a.articleCount ++ b.articleCount)
}