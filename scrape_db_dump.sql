-- MySQL dump 10.13  Distrib 5.1.49, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: scrape
-- ------------------------------------------------------
-- Server version	5.1.49-1ubuntu8.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `events`
--

DROP TABLE IF EXISTS `events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `events` (
  `InternalID` int(11) NOT NULL AUTO_INCREMENT,
  `Title` varchar(200) DEFAULT NULL,
  `ExternalID` varchar(30) DEFAULT NULL,
  `EventDate` date DEFAULT NULL,
  `StartTime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `EndTime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `Description` varchar(3000) DEFAULT NULL,
  `URL` varchar(200) DEFAULT NULL,
  `ImageURL` varchar(200) DEFAULT NULL,
  `VideoURL` varchar(200) DEFAULT NULL,
  `Location` varchar(200) DEFAULT NULL,
  `Email` varchar(50) DEFAULT NULL,
  `Phone` varchar(15) DEFAULT NULL,
  `EventHighlight` varchar(50) DEFAULT NULL,
  `EventOrganizer` varchar(50) DEFAULT NULL,
  `Cost` float DEFAULT NULL,
  PRIMARY KEY (`InternalID`)
) ENGINE=MyISAM AUTO_INCREMENT=20 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `events`
--

LOCK TABLES `events` WRITE;
/*!40000 ALTER TABLE `events` DISABLE KEYS */;
INSERT INTO `events` VALUES (1,'MICHAEL FRANTI & SPEARHEAD SOLD OUT!!!','post-70','2011-01-21','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/07/frenti-300x133.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','MICHAEL FRANTI & SPEARHEAD SOLD OUT!!!',NULL,NULL),(2,'HANNAHâ€™S HOPE BENEFIT','post-745','2011-01-22','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/A2011hhf-poster-186x300.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','HANNAHâ€™S HOPE BENEFIT',NULL,NULL),(3,'CIRCA SURVIVE & ANBERLIN','post-682','2011-01-29','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/11/ANBERLIN_CS-TOUR-ADMAT-240x300.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','CIRCA SURVIVE & ANBERLIN',NULL,NULL),(4,'HINDER','post-751','2011-02-01','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/hinder-300x177.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','HINDER',NULL,NULL),(5,'RAILROAD EARTH','post-735','2011-02-03','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/press-300x222.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','RAILROAD EARTH',NULL,NULL),(6,'THIRTY SECONDS TO MARS IS SOLD OUT!!!!!','post-670','2011-02-04','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/11/Untitled1.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','THIRTY SECONDS TO MARS IS SOLD OUT!!!!!',NULL,NULL),(7,'STREETLIGHT MANIFESTO','post-687','2011-02-10','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/11/Streetlight-Manifesto-Photo-CREDIT-MARK-R-SULLIVAN-300x200.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','STREETLIGHT MANIFESTO',NULL,NULL),(8,'WHITE CHAPEL','post-712','2011-02-17','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/photo-1-300x163.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','WHITE CHAPEL',NULL,NULL),(9,' JAGERMEISTER MUSIC TOUR Featuring: BUCKCHERRY','post-704','2011-02-18','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/Buckcherry-Cross-by-PR-Brown-199x300.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012',' JAGERMEISTER MUSIC TOUR Featuring: BUCKCHERRY',NULL,NULL),(10,'CONSPIRATOR','post-760','2011-02-19','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/Conspirator-photo-300x186.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','CONSPIRATOR',NULL,NULL),(11,'FLOGGING MOLLY','post-700','2011-02-20','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/FM-promophoto2-DanMonick-222x300.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','FLOGGING MOLLY',NULL,NULL),(12,'104.9 THE CATâ€™S FREE BIRTHDAY SHOW','post-831','2011-02-25','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2011/01/l_f3ba354f0b1245bbbbaab58f046cd5d0-300x199.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','104.9 THE CATâ€™S FREE BIRTHDAY SHOW',NULL,NULL),(13,'APOCALYPTICA','post-579','2011-03-12','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/10/Apocalyptica-Photo-2-06.29.10-300x300.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','APOCALYPTICA',NULL,NULL),(14,'ATTICUS METAL TOUR','post-835','2011-03-27','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2011/01/born-of-osiris-300x200.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','ATTICUS METAL TOUR',NULL,NULL),(15,'BADFISH','post-821','2011-04-16','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2011/01/BF1.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','BADFISH',NULL,NULL),(16,'ASKING ALEXANDRIA','post-807','2011-04-17','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2011/01/ASKINGALEX-300x100.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','ASKING ALEXANDRIA',NULL,NULL),(17,' AP TOUR','post-763','2011-05-03','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/BVB_Promo-200x300.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012',' AP TOUR',NULL,NULL),(18,'ALL TIME LOW','post-725','2011-05-05','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/alltimelow-1-300x192.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','ALL TIME LOW',NULL,NULL),(19,'REVEREND HORTON HEAT','post-779','2011-05-07','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/band-1-300x165.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','REVEREND HORTON HEAT',NULL,NULL);
/*!40000 ALTER TABLE `events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jpatilevents`
--

DROP TABLE IF EXISTS `jpatilevents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `jpatilevents` (
  `InternalID` int(11) NOT NULL DEFAULT '0',
  `Title` varchar(200) DEFAULT NULL,
  `ExternalID` varchar(30) DEFAULT NULL,
  `EventDate` date DEFAULT NULL,
  `StartTime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `EndTime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `Description` varchar(3000) DEFAULT NULL,
  `URL` varchar(200) DEFAULT NULL,
  `ImageURL` varchar(200) DEFAULT NULL,
  `VideoURL` varchar(200) DEFAULT NULL,
  `Location` varchar(200) DEFAULT NULL,
  `Email` varchar(50) DEFAULT NULL,
  `Phone` varchar(15) DEFAULT NULL,
  `EventHighlight` varchar(50) DEFAULT NULL,
  `EventOrganizer` varchar(50) DEFAULT NULL,
  `Cost` float DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jpatilevents`
--

LOCK TABLES `jpatilevents` WRITE;
/*!40000 ALTER TABLE `jpatilevents` DISABLE KEYS */;
INSERT INTO `jpatilevents` VALUES (1,NULL,'post-70','2011-01-21','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/07/frenti-300x133.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','MICHAEL FRANTI & SPEARHEAD SOLD OUT!!!',NULL,NULL),(2,NULL,'post-745','2011-01-22','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/A2011hhf-poster-186x300.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','HANNAHâ€™S HOPE BENEFIT',NULL,NULL),(3,NULL,'post-682','2011-01-29','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/11/ANBERLIN_CS-TOUR-ADMAT-240x300.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','CIRCA SURVIVE & ANBERLIN',NULL,NULL),(4,NULL,'post-751','2011-02-01','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/hinder-300x177.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','HINDER',NULL,NULL),(5,NULL,'post-735','2011-02-03','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/press-300x222.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','RAILROAD EARTH',NULL,NULL),(6,NULL,'post-670','2011-02-04','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/11/Untitled1.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','THIRTY SECONDS TO MARS IS SOLD OUT!!!!!',NULL,NULL),(7,NULL,'post-687','2011-02-10','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/11/Streetlight-Manifesto-Photo-CREDIT-MARK-R-SULLIVAN-300x200.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','STREETLIGHT MANIFESTO',NULL,NULL),(8,NULL,'post-712','2011-02-17','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/photo-1-300x163.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','WHITE CHAPEL',NULL,NULL),(9,NULL,'post-704','2011-02-18','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/Buckcherry-Cross-by-PR-Brown-199x300.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012',' JAGERMEISTER MUSIC TOUR Featuring: BUCKCHERRY',NULL,NULL),(10,NULL,'post-760','2011-02-19','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/Conspirator-photo-300x186.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','CONSPIRATOR',NULL,NULL),(11,NULL,'post-700','2011-02-20','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/FM-promophoto2-DanMonick-222x300.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','FLOGGING MOLLY',NULL,NULL),(12,NULL,'post-831','2011-02-25','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2011/01/l_f3ba354f0b1245bbbbaab58f046cd5d0-300x199.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','104.9 THE CATâ€™S FREE BIRTHDAY SHOW',NULL,NULL),(13,NULL,'post-579','2011-03-12','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/10/Apocalyptica-Photo-2-06.29.10-300x300.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','APOCALYPTICA',NULL,NULL),(14,NULL,'post-835','2011-03-27','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2011/01/born-of-osiris-300x200.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','ATTICUS METAL TOUR',NULL,NULL),(15,NULL,'post-821','2011-04-16','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2011/01/BF1.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','BADFISH',NULL,NULL),(16,NULL,'post-807','2011-04-17','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2011/01/ASKINGALEX-300x100.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','ASKING ALEXANDRIA',NULL,NULL),(17,NULL,'post-763','2011-05-03','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/BVB_Promo-200x300.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012',' AP TOUR',NULL,NULL),(18,NULL,'post-725','2011-05-05','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/alltimelow-1-300x192.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','ALL TIME LOW',NULL,NULL),(19,NULL,'post-779','2011-05-07','0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,'http://northernlightslive.com/2011/wp-content/uploads/2010/12/band-1-300x165.jpg',NULL,'1208 Route 146, Clifton Park, NY 12065',NULL,'518.371.0012','REVEREND HORTON HEAT',NULL,NULL),(20,'jitendras event',NULL,NULL,'0000-00-00 00:00:00','0000-00-00 00:00:00',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `jpatilevents` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2011-01-18 11:03:02
