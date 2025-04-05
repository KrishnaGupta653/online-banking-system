CREATE DATABASE  IF NOT EXISTS `bank` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `bank`;
-- MySQL dump 10.13  Distrib 8.0.34, for Win64 (x86_64)
--
-- Host: localhost    Database: bank
-- ------------------------------------------------------
-- Server version	8.0.34

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accounts`
--

DROP TABLE IF EXISTS `accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts` (
  `account_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `bank` varchar(100) DEFAULT NULL,
  `account_number` varchar(20) DEFAULT NULL,
  `account_type_name` varchar(100) DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `Verification_id_no` varchar(20) NOT NULL,
  `account_holder_name` varchar(100) NOT NULL,
  `contact_no` varchar(15) DEFAULT NULL,
  `email_id` varchar(255) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `encrypted_password` varchar(255) DEFAULT NULL,
  `account_opening_date` date NOT NULL,
  `balance` decimal(10,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`account_id`),
  UNIQUE KEY `account_number` (`account_number`)
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts`
--

LOCK TABLES `accounts` WRITE;
/*!40000 ALTER TABLE `accounts` DISABLE KEYS */;
INSERT INTO `accounts` VALUES (35,56611,'SBI','3943869527','Savings','2003-06-05','1212212121','Kamakshi Pandey','9198232317','krishna.gupta3657@gmail.com','GBU, Delhi','abc123','gAAAAABlOkqFHq9W0MhWZUyY8roadLy6fvtWaq-WL6T69952OpJoFVL6H--RceaoTyAquvcOfOKCELXkvQA2SKS_Nla8xPwVKg==','2023-10-26',23208.00),(37,56611,'HDFC','4439705719','Current','2003-06-05','1212212121','Kamakshi Pandey','9198232317','krishna.gupta3657@gmail.com','GBU, Delhi','123abc','gAAAAABlOpWPEBq1D5YEQKVdeVE89YzRP4-S3oz5OGJy9buWfjj8s_Imb8Pi8zmHsoADTHk6DMhkhA6GzDZ8IsKeLByb2IK7vA==','2023-10-26',2020.00),(38,3552,'SBI','4979600112','Current','2003-12-12','0962819918919','Krishna Gupta','8173905152','krishna.gupta3657@gmail.com','C Block','abc123','gAAAAABlOpaWEdw1hjaLg24KEuKBtO7_56FIVKr6DqknKOcO-hDhttv3iqR9QmTfRhk3VG4ycmcTropyUpf56v-jFTTvs4WKXg==','2023-10-26',9000.00),(39,24325,'HDFC','4528658774','Current','2003-03-03','Sachin papa','Harsh Bachha','999999999','harshdiwakar@gmail.com','uhsbjxnwcwhabcn','vodaphone','gAAAAABlPSa-dpCWPOgl_TufgncIYF1wNtmr12NruAa4fSPyFOUzwt6mjAG47ibhvKmVsCSGMswtYEzGBdvShDp5b-A_xB7ipg==','2023-10-17',10046.00),(40,65882,'HDFC','6568287530','Savings','2005-09-21','22BCE10032','Kartavya Gupta','7376396763','kavigupta2295@gmail.com','Noida','abc321','gAAAAABlQnlDGjPmhUbs3mi4Olmxujd0tNRTIkooY0Yg5FPTpHbRgPfVXYvoJOjXflHh9A6A2cOIaeSSSML8LvZxqO8_dyCY3Q==','2023-11-01',0.00),(41,65882,'ICICI','7530519663','Current','2005-09-21','22BCE10032','Kartavya Gupta','7376396763','kavigupta2295@gmail.com','Noida','321abc','gAAAAABlQnrQurWErZEqxDqnuf2Dbj70l09clCHazbQaQbpP3P4K_H4rVWhToWE7BqSwxJj832zaJ9KIYkUDjDUkCaOS-8LI_Q==','2023-11-01',99877.00),(42,43329,'PNB','6678530364','Savings','1234-08-12','12345','Polar bear','1234556','kg06052003@gmail.com','1','1234','gAAAAABlQ5L3sVcsOoyJKCFPUDjy_VhEDNCYC_9UO9GOAnDY_Nh7eo56jtBG3drSU6Z4f4cxB7h2rgWsInjjwCPZ59JI4ml_Sg==','2023-11-02',10000.00),(43,19924,'HDFC','6847348028','Current','2003-11-18','22BBS0236','Kaustubh','234567','kaustubharora082@gmail.com','1','123abc','gAAAAABlRRtphnEcUc_PNZ0TODTgtsP3f-sF8n_s0u3sVXvRqAkjun_lajtzEqeRpNkNiNjmNlVZLB92Yj201WZt1l3dcgKQFw==','2023-11-03',9000.00);
/*!40000 ALTER TABLE `accounts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `admin`
--

DROP TABLE IF EXISTS `admin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin` (
  `ad_user_id` int NOT NULL,
  `ad_name` varchar(255) NOT NULL,
  `ad_verification_id` varchar(255) NOT NULL,
  `ad_password` varchar(255) NOT NULL,
  PRIMARY KEY (`ad_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin`
--

LOCK TABLES `admin` WRITE;
/*!40000 ALTER TABLE `admin` DISABLE KEYS */;
INSERT INTO `admin` VALUES (1234,'John Gupta','22BDE1009','abc123');
/*!40000 ALTER TABLE `admin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `loan`
--

DROP TABLE IF EXISTS `loan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `loan` (
  `loan_id` int NOT NULL AUTO_INCREMENT,
  `applicant_name` varchar(255) NOT NULL,
  `date_of_birth` date NOT NULL,
  `Verification_id_no` varchar(255) DEFAULT NULL,
  `contact_no` varchar(255) DEFAULT NULL,
  `email_id` varchar(255) DEFAULT NULL,
  `address` varchar(255) NOT NULL,
  `job_title` varchar(100) DEFAULT NULL,
  `loan_type` varchar(50) NOT NULL,
  `loan_amount` decimal(10,2) NOT NULL,
  `loan_term` int NOT NULL,
  `credit_score` int DEFAULT NULL,
  `application_date` date NOT NULL,
  `status` varchar(20) DEFAULT 'Pending',
  PRIMARY KEY (`loan_id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `loan`
--

LOCK TABLES `loan` WRITE;
/*!40000 ALTER TABLE `loan` DISABLE KEYS */;
INSERT INTO `loan` VALUES (7,'Krishna Gupta','2003-05-06','22000095','8173901111','kg6512320@gmail.com','Uttar Pradesh','student','Education',1780000.00,48,789,'2023-10-10','Approved'),(8,'Sachin Sharma','1998-12-09','42318891','9178543211','ss09876@gmail.com','Bihar','accountant','Home',1000000.00,12,798,'2023-10-10','Rejected'),(9,'Harsh Gupta','1995-07-12','09876543','8456705151','hared45132@gmail.com','Himachal Pradesh','student','Personal',3500000.00,60,805,'2023-10-10','Rejected'),(10,'Ishant Shah','1988-06-05','20104578','9123987611','ishant1230973@gmail.com','Goa','lawyer','Vehicle',780000.00,24,678,'2022-10-10','Pending'),(11,'Kartavya Reddy','1985-12-09','12312369','9988776655','kreddy221@gmail.com','Kolkata','teacher','Home',500000.00,12,799,'2022-10-04','Approved'),(12,'Divyansh Sharma','1998-12-12','09876543','8173907654',NULL,'Delhi','student','Education',1600000.00,12,678,'2023-10-10','Approved'),(13,'Harsh Gupta','2002-12-03','09876541','8173905000',NULL,'Delhi','lawyer','Home',16001.00,12,799,'2023-11-06','Approved');
/*!40000 ALTER TABLE `loan` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transaction_history`
--

DROP TABLE IF EXISTS `transaction_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transaction_history` (
  `account_id` int NOT NULL,
  `user_id` varchar(255) DEFAULT NULL,
  `bank` varchar(255) DEFAULT NULL,
  `transaction_date` date NOT NULL,
  `recipient_name` varchar(255) DEFAULT NULL,
  `transaction_description` text NOT NULL,
  `recipient_type` varchar(255) DEFAULT NULL,
  `recipient_no` varchar(255) DEFAULT NULL,
  `transaction_amount` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transaction_history`
--

LOCK TABLES `transaction_history` WRITE;
/*!40000 ALTER TABLE `transaction_history` DISABLE KEYS */;
INSERT INTO `transaction_history` VALUES (35,'56611','SBI','2023-11-01','xyz','123','account','abc123',0.00),(35,'56611','SBI','2023-11-01','xyz','123','account','abc123',0.00),(40,'65882','HDFC','2023-11-01','krishna','Udhar','account','11111111987',100000.00),(41,'65882','ICICI','2023-11-01','Tejasv','Loan','phone','06969696969',123.00),(43,'19924','HDFC','2023-11-03','Manas','Laoan','account','123',1000.00),(38,'3552','SBI','2023-11-06','Manas','Laoan','account','11111111',1000.00);
/*!40000 ALTER TABLE `transaction_history` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-11-07  2:38:17
