package hack.classes

trait Semigroup[E] {
  def op(a: E, b: E): E
}
