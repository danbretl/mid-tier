DROP TABLE IF EXISTS `abexmid`.`scraped_events_vw`;
CREATE OR REPLACE VIEW `abexmid`.`scraped_events_vw` AS
SELECT *
  FROM `scrape`.`events`
;