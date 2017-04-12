package hack

import java.io.{InputStream, OutputStream, PrintStream}

import com.fasterxml.jackson.databind.MappingIterator
import com.fasterxml.jackson.dataformat.csv.{CsvMapper, CsvSchema}

import scala.collection.{BitSet, mutable}

object IO {

  def readFile(io: InputStream): (Map[Int, BitSet], Map[ArticleId, String], Map[CategoryId, String]) = {
    val mapper = new CsvMapper()
    val schema = CsvSchema.emptySchema.withHeader

    val it: MappingIterator[java.util.Map[String, String]] = mapper
      .readerFor(classOf[java.util.Map[String, String]])
      .`with`(schema)
      .readValues(io)

    val articles    = mutable.Map.empty[CategoryId, mutable.BitSet]
    val articleIds  = mutable.Map.empty[String, ArticleId]
    val categoryIds = mutable.Map.empty[String, CategoryId]

    while (it.hasNext) {
      val row = it.next()
      val art = row.get("article")
      val cat = row.get("category")

      if (!articleIds.contains(art))
        articleIds.put(art, articleIds.size)

      if (!categoryIds.contains(cat))
        categoryIds.put(cat, categoryIds.size)

      val catId = categoryIds(cat)

      if (!articles.contains(catId))
        articles.put(catId, mutable.BitSet.empty)

      articles(catId).add(articleIds(art))
    }

    (articles.mapValues(b => b.toImmutable).toMap,
      categoryIds.map(_.swap).toMap,
      articleIds.map(_.swap).toMap)
  }

  def writeFile(io:           PrintStream
                , s:          State
                , categories: Map[CategoryId, String]
                , articles:   Map[ArticleId, String]): Unit = {
    val q = "\""

    io.println("category,article")
    for ((c, a) <- s.pairs)
      io.println(q + categories(c) + q + "," + q + articles(a) + q)
  }
}
