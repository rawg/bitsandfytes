name := "hack"

version := "1.0"

scalaVersion := "2.11.8"

mainClass := Some("hack.Main")

assemblyJarName := "hack.jar"

libraryDependencies +=
  "com.fasterxml.jackson.dataformat" % "jackson-dataformat-csv" % "2.7.0"

scalacOptions ++= Seq("-Xdisable-assertions", "-Xlint", "-deprecation")
