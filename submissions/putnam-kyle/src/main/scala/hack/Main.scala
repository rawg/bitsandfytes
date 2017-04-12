package hack

import scala.util.Random

object Main {

  val rnd = new Random(0xCAFEF00D)

  def main(args: Array[String]): Unit = {
    val (as, cNames, aNames) = IO.readFile(System.in)
    val s = State.fromArticles(as)

    warn("Parsed %d articles and %d categories (%d pairs)".format(aNames.size, cNames.size, s.pairs.length))

    val best = args.toList match {
      case "-b" :: breadth :: _ =>
        searchStates(s, Integer.parseInt(breadth))
      case _ =>
        searchStates(s, 40)
    }

    IO.writeFile(System.out, best.state, cNames, aNames)
    //warn("check: %d pairs".format(best.state.pairs.length))
  }

  type Fitness = Int

  case class Activation
    ( path:            List[Operation]
    , nextOp:          Operation // not yet in `path`
    , removedPairs:    Int
    , previousFitness: Fitness
    , currentFitness:  Fitness
    , state:           State
    )

  def searchStates(s: State, breadth: Int): Activation = {
    val x = s.allowedOperations.map(_.removedPairs).sum
    var active = Vector(Activation(List.empty, NoOp, 0, x, x, s))
    var paused = Vector.empty[Activation]

    var countIters  = 0
    var countStates = 0
    var best = active(0)

    while (active.nonEmpty) {
      warn("iteration %d".format(countIters))
      countIters += 1

      for (a <- active) {
        countStates += 1

        /*warn("%s %5d : %5d : %s%s %s".format(
          if (a.removedPairs > best.removedPairs) "*" else " ",
          a.removedPairs + a.nextOp.removedPairs, a.currentFitness,
          if (countIters > 9) "..." else "", a.path.take(9).reverse, a.nextOp))*/

        if (a.removedPairs > best.removedPairs)
          best = a

        paused ++= select(successors(a), breadth, rnd)
        if (paused.length > 10 * breadth)
          paused = select(paused, breadth, rnd)
      }

      active = select(paused, breadth, rnd)
      paused = Vector.empty[Activation]
    }

    warn("")
    warn(("%d removed pairs, %d iterations, %d states," +
      " %d remove ops, %d merge ops").format(
      best.removedPairs, countIters, countStates,
      best.path.count { case Remove(_, _) => true; case _ => false },
      best.path.count { case Merge(_, _, _) => true; case _ => false }))
    warn("check: %d".format(best.path.map(_.removedPairs).sum))

    best
  }

  def successors(current: Activation): Vector[Activation] = {
    val nextState        = Eval.run(current.state, current.nextOp)
    val nextPath         = current.nextOp :: current.path
    val nextRemovedPairs = current.removedPairs + current.nextOp.removedPairs
    val nextFitness      = nextRemovedPairs + nextState.allowedOperations.map(_.removedPairs).sum

    // The "running sum" starts with this "zero" element
    val noOp = Activation(
      nextPath,
      NoOp,
      nextRemovedPairs,
      nextFitness,
      nextFitness,
      nextState)

    val opCosts = null // estimateOpCosts(NoOp +: nextState.allowedOperations)
    nextState.allowedOperations.scanLeft(noOp)(scanOp(nextPath, nextRemovedPairs, opCosts, nextState)).tail
  }

  // Update the "running sum" of activation records
  private def scanOp(path:       List[Operation]
                     , score:    Int
                     , estCosts: Map[CategoryId, OpCost]
                     , state:    State)
                    (q: Activation, op: Operation) = {
    // Operations are ordered by category, and executing this operation implies
    // we chose not to execute the ones for previous categories. We adjust the
    // running estimate of the final score downward by the number of pairs we
    // can no longer remove as the result of implicitly skipping the previous
    // operations.
    val previousDelta =
      if (ordering(op) > ordering(q.nextOp)) // q.nextOp is the previous Activation's op
        0 // estCosts(ordering(q.nextOp)).ifNeither
      else 0

    op match {
      case Remove(x, _) =>
        Activation(path, op, score,
          q.previousFitness
            - previousDelta,
          q.previousFitness
            //- estCosts(x).ifRemoved
            - previousDelta,
          state)

      case Merge(x, y, _) =>
        Activation(path, op, score,
          q.previousFitness
            - previousDelta,
          q.previousFitness
            //- (estCosts(x).ifMerged max estCosts(y).ifMerged)
            - previousDelta,
          state)
    }
  }

  case class OpCost
    ( ifRemoved: Int
    , ifMerged:  Int
    , ifNeither: Int
    )

  def estimateOpCosts(ops: Vector[Operation]): Map[CategoryId, OpCost] = {
    val pairs = ops.foldLeft(List.empty[(CategoryId, Operation)]) {
      case (xs, m@NoOp)           => (0, m) :: xs
      case (xs, m@Remove(x, _))   => (x, m) :: xs
      case (xs, m@Merge(x, y, _)) => (x, m) :: (y, m) :: xs }

    pairs.groupBy(_._1).mapValues { ms =>
      val (removes, merges) = ms.partition {
        case (_, Remove(_, _)) => true
        case _                 => false
      }

      // If we remove `x`, we cannot later merge anything with it, so the
      // newly immutable pairs shouldn't be counted. Suppose there are two
      // merges: a = x and b = x. Since `a` must share 75% of articles with
      // `x`, and `b` must share 75% of articles with `x`, `a` and `b` cannot
      // be disjoint. This means the largest number of now-immutable pairs
      // is less than a.removedPairs + b.removedPairs
      //
      // If `x` and all the other merges involving `x` share exactly the
      // same set of articles, then the number of now-immutable pairs is
      // no smaller than the number of pairsRemoved by any merge operation.
      //
      // This means ifRemoved must be at least x.removedPairs and at most
      // a.removedPairs + b.removedPairs (+ c.removedPairs + ...)
      val ifRemoved = if (merges.nonEmpty) merges.map(_._2.removedPairs).max else 0

      // Merging is mutually exclusive with removing, and there is either
      // zero or one remove operations on this column; if we merge now we
      // can be sure we can't remove it later
      val ifMerged = removes.map(_._2.removedPairs).sum

      // Example: Remove(0),Merge(0,3),Merge(0,4) if we decide to skip past
      // these operations on category 0 then we know for sure the articles
      // in category 0 can't be removed; articles in 3 or 4 won't be merged
      // with 0 (eg Merge(3,0) or Merge(4,0)) later
      val ifNeither = ifRemoved + ifMerged

      OpCost(ifRemoved, ifMerged, ifNeither)
    }
  }

  private def ordering(m: Operation): Int = m match {
    case NoOp           => 0
    case Remove(x, _)   => x
    case Merge(x, y, _) => x min y }

  private def select(xs: Vector[Activation], n: Int, rnd: Random): Vector[Activation] =
    xs.sortBy(-_.currentFitness).take(n)

  private def warn(s: String): Unit =
    System.err.println(s)

}
