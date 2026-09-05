// ============================================================
// CLC Historico 2024-2025 -> Neo4j AuraDB
// Sube esta carpeta a GitHub (raw URLs) o usa el Data Importer
// de Aura y apunta cada bloque a su CSV correspondiente.
// Reemplaza https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/Grafos/neo4j_export por tu URL raw de GitHub, ej:
// https://raw.githubusercontent.com/usuario/repo/main/neo4j_export
// ============================================================

// ---- Constraints (evitan duplicados en re-cargas) ----
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Tournament) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Edition) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Stage) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Team) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:TeamName) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Player) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Match) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Award) REQUIRE n.id IS UNIQUE;

// ---- NODOS ----
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/nodes/tournaments.csv' AS row
MERGE (n:Tournament {id: row.TOURNAMENT_ID})
SET n.name = row.NAME, n.shortName = row.SHORT_NAME, n.venue = row.VENUE, n.notes = row.NOTES;

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/nodes/editions.csv' AS row
MERGE (n:Edition {id: row.EDITION_ID})
SET n.year = row.YEAR, n.name = row.NAME, n.format = row.FORMAT, n.status = row.STATUS;

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/nodes/stages.csv' AS row
MERGE (n:Stage {id: row.STAGE_ID})
SET n.name = row.NAME, n.order = toInteger(row.ORDER);

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/nodes/teams.csv' AS row
MERGE (n:Team {id: row.TEAM_ID})
SET n.name = row.CANONICAL_NAME, n.active2026 = row.ACTIVE_2026, n.notes = row.NOTES;

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/nodes/team_names.csv' AS row
MERGE (n:TeamName {id: row.NAME_ID})
SET n.name = row.NAME, n.nameType = row.NAME_TYPE;

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/nodes/players.csv' AS row
MERGE (n:Player {id: row.PLAYER_ID})
SET n.name = row.CANONICAL_NAME, n.identityStatus = row.IDENTITY_STATUS,
    n.identityMethod = row.IDENTITY_METHOD, n.confidence = row.CONFIDENCE, n.notes = row.NOTES;

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/nodes/matches.csv' AS row
MERGE (n:Match {id: row.MATCH_ID})
SET n.fecha = toInteger(row.FECHA), n.partido = row.PARTIDO, n.specialName = row.SPECIAL_NAME,
    n.cancha = row.CANCHA, n.hora = row.HORA,
    n.goalsTeam1 = toFloat(row.GOALS_TEAM_1), n.goalsTeam2 = toFloat(row.GOALS_TEAM_2),
    n.resultTeam1 = row.RESULT_TEAM_1, n.resultTeam2 = row.RESULT_TEAM_2,
    n.winnerTeamId = row.WINNER_TEAM_ID, n.resolutionMethod = row.RESOLUTION_METHOD,
    n.dataQualityStatus = row.DATA_QUALITY_STATUS, n.sourceFile = row.SOURCE_FILE;

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/nodes/awards.csv' AS row
MERGE (n:Award {id: row.AWARD_RECORD_ID})
SET n.type = row.AWARD_TYPE, n.name = row.AWARD_NAME, n.derivation = row.DERIVATION,
    n.identityConfidence = row.IDENTITY_CONFIDENCE;

// ---- RELACIONES ----
LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/edition_part_of_tournament.csv' AS row
MATCH (a:Edition {id: row.`:START_ID`}), (b:Tournament {id: row.`:END_ID`})
MERGE (a)-[:PART_OF]->(b);

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/match_in_edition.csv' AS row
MATCH (a:Match {id: row.`:START_ID`}), (b:Edition {id: row.`:END_ID`})
MERGE (a)-[:IN_EDITION]->(b);

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/match_at_stage.csv' AS row
MATCH (a:Match {id: row.`:START_ID`}), (b:Stage {id: row.`:END_ID`})
MERGE (a)-[:AT_STAGE]->(b);

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/team_played_match.csv' AS row
MATCH (a:Team {id: row.`:START_ID`}), (b:Match {id: row.`:END_ID`})
MERGE (a)-[r:PLAYED_MATCH]->(b)
SET r.goals = toFloat(row.GOALS), r.result = row.RESULT, r.side = toInteger(row.SIDE);

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/team_participated_in_edition.csv' AS row
MATCH (a:Team {id: row.`:START_ID`}), (b:Edition {id: row.`:END_ID`})
MERGE (a)-[:PARTICIPATED_IN]->(b);

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/team_reached_stage.csv' AS row
MATCH (a:Team {id: row.`:START_ID`}), (b:Stage {id: row.`:END_ID`})
MATCH (e:Edition {id: row.EDITION_ID})
MERGE (a)-[r:REACHED_STAGE {editionId: row.EDITION_ID}]->(b)
SET r.stageOrder = toInteger(row.STAGE_ORDER);

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/team_used_name.csv' AS row
MATCH (a:Team {id: row.`:START_ID`}), (b:TeamName {id: row.`:END_ID`})
MERGE (a)-[:USED_NAME]->(b);

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/player_scored_in_edition.csv' AS row
MATCH (a:Player {id: row.`:START_ID`}), (b:Edition {id: row.`:END_ID`})
MERGE (a)-[r:SCORED_IN]->(b)
SET r.goals = toInteger(row.GOALS), r.teamId = row.TEAM_ID, r.confidence = row.IDENTITY_CONFIDENCE;

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/player_carded_in_match.csv' AS row
MATCH (a:Player {id: row.`:START_ID`}), (b:Match {id: row.`:END_ID`})
MERGE (a)-[r:CARDED_IN]->(b)
SET r.teamId = row.TEAM_ID, r.yellowCards = toInteger(row.YELLOW_CARDS),
    r.redCards = toInteger(row.RED_CARDS), r.redCardType = row.RED_CARD_TYPE,
    r.confidence = row.IDENTITY_CONFIDENCE;

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/player_played_for_team.csv' AS row
MATCH (a:Player {id: row.`:START_ID`}), (b:Team {id: row.`:END_ID`})
MERGE (a)-[r:PLAYED_FOR {editionId: row.EDITION_ID}]->(b);

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/award_for_team.csv' AS row
MATCH (a:Award {id: row.`:START_ID`}), (b:Team {id: row.`:END_ID`})
MERGE (a)-[:FOR_TEAM]->(b);

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/award_in_edition.csv' AS row
MATCH (a:Award {id: row.`:START_ID`}), (b:Edition {id: row.`:END_ID`})
MERGE (a)-[:IN_EDITION]->(b);

LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/main/neo4j_export/relationships/player_won_award.csv' AS row
MATCH (a:Player {id: row.`:START_ID`}), (b:Award {id: row.`:END_ID`})
MERGE (a)-[:WON]->(b);
