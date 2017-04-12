package hack

object Eval {

  def run(s: State, m: Operation): State = m match {
    case NoOp           => s
    case Remove(a, _)   => runRemove(s, a)
    case Merge(a, b, _) => runMerge(s, a, b)
  }

  private def runRemove(s: State, a: CategoryId) = {
    // `a` is not already merged with another category
    assert(s.categories.root(a) == a)
    assert(s.categories.label(a).size == 1)

    // Removing `a` doesn't orphan any articles
    assert(s.articles(a).forall(s.categoryCount(_) > 1))

    // This operation was among the allowed set of operations
    assert(1 == s.allowedOperations.count {
      case Remove(c, _) => c == a
      case _            => false })

    val categoryCount = // Decrement each article in `a`
      s.categoryCount ++ s.articles(a).map(x => (x, s.categoryCount(x) - 1))

    val pendingMoves = s.allowedOperations.map {
      case m@Remove(x, _) if x > a =>
        // How many articles in category `x` belong to only one or two other categories?
        val one = s.articles(x).count(categoryCount(_) == 1)
        val two = 0 // articles(x).count(categoryCount(_) == 2)

        // If an article belongs to two categories, and one of them is `x`, it will belong
        // to only one after removing `x`. Thus removing `x` "locks" the remaining pair
        if (one == 0) Option(m /*.copy(pairsLocked = two)*/) else Option.empty

      case m@Merge(x, y, _) if x > a && y > a =>
        // Articles belonging *only* to x and y will have only one category remaining
        // after merging x = y, so they could no longer be removed
        val two = 0 // (articles(x) | articles(y)).count(categoryCount(_) == 2)
        Option(m /*.copy(pairsLocked = two)*/)

      case _ => Option.empty
    }.collect { case Some(p) => p }

    State(
      s.articles - a,
      categoryCount,
      s.categories,
      pendingMoves)
  }

  private def runMerge(s: State, a: CategoryId, b: CategoryId) = {
    // `a` and `b` are homogenous
    assert(State.homogenous(s.articles(a), s.articles(b)))

    // `a` and `b` don't already belong to same super category
    assert(s.categories.root(a) != s.categories.root(b))

    // This operation was among the allowed set of operations
    assert(1 == s.allowedOperations.count {
      case Merge(x, y, _) => x == a && y == b
      case _              => false })

    val categoryCount = // Decrement articles that are in both `a` and `b`
      s.categoryCount ++ (s.articles(a) & s.articles(b)).map(x => (x, s.categoryCount(x) - 1))

    val categories =
      s.categories.union(a, b)

    val c = if (a < b) a else b

    val allowedOperations = s.allowedOperations.map {
      // Don't allow removing of the two categories we just merged
      case m@Remove(x, _) if x > c && x != a && x != b =>
        // If an article belongs to two categories, and one of them is `x`, it will belong
        // to only one after removing `x`. Thus removing `x` "locks" the remaining pair
        val two = 0 //s.articles(x).count(categoryCount(_) == 2)
        Option(m /*.copy(pairsLocked = two)*/)

      // No reason to merge x = y if they now belong to the a = b = x = y category
      case m@Merge(x, y, _) if (x > a || (x == a && y > b)) &&
        !s.categories.connected(x, y) =>

        // Articles belonging *only* to x and y will have only one category remaining
        // after merging x = y, so they could no longer be removed
        val two = 0 //(s.articles(x) | s.articles(y)).count(categoryCount(_) == 2)
        Option(m /*.copy(pairsLocked = two)*/)

      case _ => Option.empty
    }.collect { case Some(p) => p }

    State(
      s.articles,
      categoryCount,
      categories,
      allowedOperations)
  }

}
