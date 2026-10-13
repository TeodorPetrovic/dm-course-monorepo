-- Lokalna šema za dm-frontend (MariaDB/MySQL 8 kompatibilno). Usklađena sa drizzle šemama u
-- dm-frontend/server/database/schemas/*.ts i sa Day 1 event šemom (12 polja).
SET NAMES utf8mb4;
DROP TABLE IF EXISTS event;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS seo;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS `user`;

CREATE TABLE category (
  category_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  img_url TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE seo (
  seo_id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(60) NOT NULL,
  description VARCHAR(155) NOT NULL,
  key_words JSON NOT NULL
);

CREATE TABLE product (
  product_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  img_url TEXT NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  category_id INT NOT NULL,
  price DECIMAL(10,2) NULL,
  seo_id INT NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_product_seo FOREIGN KEY (seo_id) REFERENCES seo(seo_id),
  CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES category(category_id),
  INDEX idx_product_category (category_id)
);

-- Day 1: proširena event tabela (stara polja event_type/user_session/product_id ostaju)
CREATE TABLE event (
  event_id INT PRIMARY KEY AUTO_INCREMENT,
  event_type VARCHAR(50) NOT NULL,
  user_id INT NULL,
  user_session VARCHAR(255) NOT NULL,
  product_id INT NULL,
  category_id INT NULL,
  price DECIMAL(10,2) NULL,
  quantity INT NOT NULL DEFAULT 1,
  source VARCHAR(32) NOT NULL DEFAULT 'product_page',
  `timestamp` DATETIME NOT NULL,
  recommendation_source VARCHAR(32) NULL,
  recommendation_position INT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_event_session (user_session),
  INDEX idx_event_type (event_type),
  INDEX idx_event_product (product_id)
);

CREATE TABLE `user` (
  user_id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  password VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
