package hack

import scala.annotation.tailrec
import scala.collection.BitSet

object State {

  def fromArticles(articles: Map[CategoryId, BitSet]): State = {
    import hack.instances.super_._

    val categoryCount =
      articles.values.map(as => as.map(a => (a, 1)).toMap).reduce(combineCounts[ArticleId])

    val categories =
      DisjointSet.fromLabels(articles.map { case(c, as) =>
        (c, Super.singleton(c, as)) })

    val pendingMerges =
      mergeable[CategoryId](articles).map { case (a, b) =>
        Merge(a, b, (articles(a) & articles(b)).size) }

    val pendingRemoves =
      articles.filter { case (_, as) => as.forall(a => categoryCount(a) > 1) }
        .map { case (c, as) => Remove(c, as.size) }.toVector

    val pendingMoves =
      (pendingMerges ++ pendingRemoves).sortBy {
        case Remove(x, _)   => x
        case Merge(x, y, _) => x min y }

    State(
      articles,
      categoryCount,
      categories,
      pendingMoves)
  }

  def combineCounts[K](a: Map[K, Int], b: Map[K, Int]): Map[K, Int] =
    a ++ b.map { case (k, v) => (k, v + a.getOrElse(k, 0)) }

  def mergeable[K: Ordering](articles: Map[K, BitSet]): Vector[(K, K)] =
    combinations(articles.keys.toList.sorted).filter { case (a, b) =>
      homogenous(articles(a), articles(b)) }.toVector

  def combinations[A](xs: List[A]): Iterator[(A, A)] = {
    @tailrec
    def go(xs: List[A], it: Iterator[(A, A)]): Iterator[(A, A)] = xs match {
      case h :: t => go(t, it ++ t.map(t => (h, t)).iterator)
      case _      => it
    }
    go(xs, Iterator.empty)
  }

  def homogenous(a: BitSet, b: BitSet): Boolean = {
    val aSize = a.size.toFloat
    val bSize = b.size.toFloat

    // Assume a ⊆ b, then |a|/|b| is the maximum possible Jaccard
    // similarity. If this is small, no need to compute real thing
    if (aSize / bSize <= 0.75) return false
    if (bSize / aSize <= 0.75) return false

    (a & b).size.toFloat / (a | b).size.toFloat > 0.75
  }
}

case class State
  ( articles:           Map[CategoryId, BitSet]
  , categoryCount:      Map[ArticleId, Int]
  , categories:         DisjointSet[CategoryId, Super]
  , allowedOperations:  Vector[Operation]
  ) {

  def pairs: List[(CategoryId, ArticleId)] = {
    val all = categories.roots.map(categories.label)
    val oks = all.filter(c => articles.contains(c.id)).toList

    oks.flatMap { c =>
      val c_id = c.id
      c.articles.map(a => (c_id, a)) }
  }
}