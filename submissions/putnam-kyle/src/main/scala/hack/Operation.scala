package hack

abstract sealed class Operation {
  def removedPairs: Int
}

case object NoOp extends Operation {
  @Override
  def removedPairs: Int = 0
}

case class Remove
  ( category: Int
  , @Override removedPairs: Int )
  extends Operation

case class Merge
  ( aCategory: Int
  , bCategory: Int
  , @Override removedPairs: Int )
  extends Operation