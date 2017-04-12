package hack

import scala.collection.BitSet

object Super {
  def singleton(categoryId: Int, articles: BitSet): Super =
    Super(articles, Set(categoryId), Map(categoryId -> articles.size))
}

case class Super
  ( articles:     BitSet
  , categories:   Set[CategoryId]
  , articleCount: Map[ArticleId, Int]
  ) {
  def id: CategoryId = articleCount.maxBy(_._2)._1
  def size: Int      = articles.size
}