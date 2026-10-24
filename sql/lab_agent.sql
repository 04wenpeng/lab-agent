-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: lab_agent
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `equipments`
--

DROP TABLE IF EXISTS `equipments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `equipments` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `lab_id` int NOT NULL COMMENT '所属实验室',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备名称',
  `description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '说明',
  `img` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '图片',
  `spec` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '型号规格',
  `quantity` int NOT NULL COMMENT '数量',
  `status` int NOT NULL COMMENT '状态：0-维修，1-正常',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `lab_id` (`lab_id`),
  CONSTRAINT `equipments_ibfk_1` FOREIGN KEY (`lab_id`) REFERENCES `labs` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='实验室设备表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `equipments`
--

LOCK TABLES `equipments` WRITE;
/*!40000 ALTER TABLE `equipments` DISABLE KEYS */;
INSERT INTO `equipments` VALUES (1,1,'RTX4090','深度学习训练显卡','/uploads/1789556233224_ed47597b.png','24G 显存',2,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(2,1,'开发主机','学生上机编程','/uploads/1789556233224_ed47597b.png','i7 / 32G / 1T SSD',20,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(3,1,'投影仪','讲课演示','/uploads/1789556233224_ed47597b.png','1080P',1,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(4,1,'千兆交换机','机房组网','/uploads/1789556233224_ed47597b.png','24 口',1,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(5,2,'示波器','电路波形观测','/uploads/1789556233224_ed47597b.png','100MHz 双通道',8,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(6,2,'信号发生器','信号源实验','/uploads/1789556233224_ed47597b.png','DDS 60MHz',6,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(7,2,'数字万用表','电子测量','/uploads/1789556233224_ed47597b.png','4 位半',10,0,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(8,2,'直流稳压电源','电路供电','/uploads/1789556233224_ed47597b.png','30V 5A',8,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(9,3,'光学实验台','几何光学实验','/uploads/1789556233224_ed47597b.png','1.2m 隔振台',4,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(10,3,'氦氖激光器','干涉衍射实验','/uploads/1789556233224_ed47597b.png','632.8nm',2,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(11,3,'力学轨道','牛顿定律实验','/uploads/1789556233224_ed47597b.png','气垫导轨 1.5m',3,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(12,3,'分光计','光谱测量','/uploads/1789556233224_ed47597b.png','0.1° 精度',4,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(13,4,'电子天平','试剂称量','/uploads/1789556233224_ed47597b.png','0.1mg',6,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(14,4,'离心机','样品分离','/uploads/1789556233224_ed47597b.png','4000rpm',2,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(15,4,'通风橱','有机实验','/uploads/1789556233224_ed47597b.png','1.5m',3,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(16,4,'pH 计','溶液酸碱度','/uploads/1789556233224_ed47597b.png','0.01pH',4,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(17,5,'显微镜','细胞观察','/uploads/1789556233224_ed47597b.png','1000x 光学',10,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(18,5,'恒温培养箱','菌种培养','/uploads/1789556233224_ed47597b.png','室温 ~ 60℃',2,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(19,5,'移液器','微量取样','/uploads/1789556233224_ed47597b.png','0.5-10μL',20,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(20,5,'PCR 仪','基因扩增','/uploads/1789556233224_ed47597b.png','96 孔',1,0,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(21,6,'GPU 训练服务器','大模型微调','/uploads/1789556233224_ed47597b.png','2 * RTX4090 / 128G',1,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(22,6,'RTX4090','深度学习训练显卡','/uploads/1789556233224_ed47597b.png','24G 显存',4,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(23,6,'深度相机','视觉数据采集','/uploads/1789556233224_ed47597b.png','RealSense D435i',3,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(24,6,'标注工作站','数据集标注','/uploads/1789556233224_ed47597b.png','i9 / 64G',6,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(25,7,'UR5 机械臂','工业机械臂教学','/uploads/1789556233224_ed47597b.png','负载 5kg',2,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(26,7,'Livox 激光雷达','SLAM 建图','/uploads/1789556233224_ed47597b.png','Mid-360',3,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(27,7,'RealSense 深度相机','视觉抓取','/uploads/1789556233224_ed47597b.png','D435i',4,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(28,7,'Jetson Orin','边缘计算','/uploads/1789556233224_ed47597b.png','32G',4,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(29,8,'开发主机','项目实训','/uploads/1789556233224_ed47597b.png','i7 / 32G / 1T SSD',40,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(30,8,'显示器','双屏开发','/uploads/1789556233224_ed47597b.png','27 寸 2K',40,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(31,8,'投影仪','答辩演示','/uploads/1789556233224_ed47597b.png','1080P',2,1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(32,8,'代码服务器','Git 与 CI','/uploads/1789556233224_ed47597b.png','8 核 / 32G',1,1,'2026-09-16 18:56:36','2026-09-16 18:57:14');
/*!40000 ALTER TABLE `equipments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `labs`
--

DROP TABLE IF EXISTS `labs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `labs` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '名称',
  `description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '简介',
  `img` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '封面',
  `location` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '位置',
  `capacity` int NOT NULL COMMENT '容量',
  `open_time` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '开放开始时间',
  `close_time` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '开放结束时间',
  `status` int NOT NULL COMMENT '状态, 0-关闭，1-开放',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='实验室信息';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `labs`
--

LOCK TABLES `labs` WRITE;
/*!40000 ALTER TABLE `labs` DISABLE KEYS */;
INSERT INTO `labs` VALUES (1,'计算机实验室','计算机实验室','/uploads/1789531451048_96e733ca.png','综合实验楼102',20,'09:00','18:00',1,'2026-09-16 11:32:38','2026-09-16 12:04:27'),(2,'电子实验室','电子实验室','/uploads/1789531112623_bd29218a.png','综合实验楼201',20,'08:00','18:00',1,'2026-09-16 11:59:04','2026-09-16 12:04:06'),(3,'物理实验室','物理实验室','/uploads/1789531179107_417a4eef.png','综合实验楼101',20,'08:00','18:00',1,'2026-09-16 11:59:52','2026-09-16 12:03:56'),(4,'化学实验室','化学实验室','/uploads/1789531112623_bd29218a.png','综合实验楼301',20,'08:00','18:00',1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(5,'生物实验室','生物实验室','/uploads/1789531112623_bd29218a.png','综合实验楼302',20,'08:00','18:00',1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(6,'人工智能实验室','人工智能实验室','/uploads/1789531112623_bd29218a.png','综合实验楼401',30,'08:00','18:00',1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(7,'机器人实验室','机器人实验室','/uploads/1789531112623_bd29218a.png','综合实验楼402',20,'09:00','17:00',1,'2026-09-16 18:56:36','2026-09-16 18:56:36'),(8,'软件工程实验室','软件工程实验室','/uploads/1789531112623_bd29218a.png','综合实验楼501',40,'08:00','20:00',1,'2026-09-16 18:56:36','2026-09-16 18:56:36');
/*!40000 ALTER TABLE `labs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reservations`
--

DROP TABLE IF EXISTS `reservations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reservations` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` int NOT NULL COMMENT '预约人',
  `lab_id` int NOT NULL COMMENT '实验室',
  `equipment_id` int DEFAULT NULL COMMENT '设备，空表示预约实验室',
  `date` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '预约日期',
  `start_time` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '开始时间',
  `end_time` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '结束时间',
  `remark` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `status` int NOT NULL COMMENT '预约状态 0待审核，1已通过，2已拒绝，3已取消',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `lab_id` (`lab_id`),
  KEY `equipment_id` (`equipment_id`),
  CONSTRAINT `reservations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `reservations_ibfk_2` FOREIGN KEY (`lab_id`) REFERENCES `labs` (`id`),
  CONSTRAINT `reservations_ibfk_3` FOREIGN KEY (`equipment_id`) REFERENCES `equipments` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预约信息';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reservations`
--

LOCK TABLES `reservations` WRITE;
/*!40000 ALTER TABLE `reservations` DISABLE KEYS */;
INSERT INTO `reservations` VALUES (1,4,8,NULL,'2026-09-17','15:00','16:00','',3,'2026-09-17 14:53:58','2026-09-18 10:31:46'),(2,4,8,NULL,'2026-09-18','09:00','18:00','',3,'2026-09-17 14:55:50','2026-09-18 18:00:06'),(3,4,8,NULL,'2026-09-19','09:00','18:00','',3,'2026-09-17 14:56:14','2026-09-20 09:16:04'),(4,4,8,NULL,'2026-09-20','09:00','18:00','111',3,'2026-09-17 14:57:01','2026-09-20 18:00:09'),(5,4,8,NULL,'2026-09-22','09:00','18:00','2222',0,'2026-09-17 15:00:21','2026-09-17 15:00:21'),(6,4,8,32,'2026-09-18','09:00','18:00','',3,'2026-09-17 15:11:34','2026-09-17 16:34:03'),(7,4,8,32,'2026-09-19','09:00','18:00','',3,'2026-09-17 15:12:24','2026-09-17 16:33:33'),(8,3,7,NULL,'2026-09-18','09:00','15:00','',2,'2026-09-17 16:39:55','2026-09-17 16:47:09'),(9,3,7,26,'2026-09-18','09:00','12:00','',1,'2026-09-17 16:40:24','2026-09-17 16:46:30'),(10,4,6,NULL,'2026-09-19','09:00','16:00','',3,'2026-09-18 10:12:56','2026-09-20 09:16:04'),(11,4,3,NULL,'2026-09-21','14:00','15:00',NULL,0,'2026-09-20 16:31:25','2026-09-20 16:31:25'),(12,4,5,17,'2026-09-22','14:00','16:00',NULL,0,'2026-09-20 16:33:35','2026-09-20 16:33:35'),(13,4,4,13,'2026-09-21','16:00','18:00',NULL,0,'2026-09-20 16:42:03','2026-09-20 16:42:03'),(14,4,3,NULL,'2026-09-22','14:00','18:00',NULL,0,'2026-09-21 12:59:51','2026-09-21 12:59:51');
/*!40000 ALTER TABLE `reservations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号',
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '名称',
  `role` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色：student-学生，admin-管理员',
  `email` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '邮箱',
  `phone` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手机号',
  `avatar` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '头像',
  `status` int NOT NULL COMMENT '状态：0-禁用，1-正常',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户信息表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin','$2b$12$ypJClLKejFCsyn2eltOco.YAmXory0HFjh7E/oHu9MBzDZZ6wYSSi','管理员1','admin','xxx@xxx.cn','13988776689','/uploads/1789377370709_df5418ea.png',1,'2026-09-11 15:30:07','2026-09-16 10:49:56'),(2,'bbb','$2b$12$xJCHORaQz3in/urOkvh1keHA0ofZ.IfPZbzE0xiWtHPJneUD/AnBi','bbb','student',NULL,NULL,NULL,0,'2026-09-11 15:28:02','2026-09-11 15:28:02'),(3,'ccc','$2b$12$zcyt.i5fB4cFKxm4myUGfu/PM26KDTwwKYr3jEr4qDS2MDOr0vijK','小白白','student',NULL,NULL,'/uploads/1789634367282_cc695a76.png',1,'2026-09-11 15:29:12','2026-09-17 16:39:34'),(4,'aaa','$2b$12$XBannp3IBgKGr0dJ/LB09uXfZTWSTasVaUv4v4CD0ERBVSqPMRQP2','李四','student','lisi@qq.com','13899776688','/uploads/1789609868750_fbabf94d.jpg',1,'2026-09-09 16:56:41','2026-09-17 09:51:10'),(9,'www','$2b$12$WyjBvK8sLFr79ZtXdawDbOtmwP/x6Z68umZ3XCWyTfjW1ch/aODzm','小王','student','','','',1,'2026-09-15 18:40:28','2026-09-15 18:40:28'),(10,'xiaowu','$2b$12$0.XQWUriNJuntnaug3SIw.p1.es6jbZ4EehwCcooyrrSlPMuontBy','小五','student','xiaowu@163.com','13677886677','',1,'2026-09-15 18:50:06','2026-09-15 18:50:06');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'lab_agent'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-21 14:44:27
