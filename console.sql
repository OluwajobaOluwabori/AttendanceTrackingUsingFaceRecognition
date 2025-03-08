
create table ass3.detected_faces
(
    id            int auto_increment
        primary key,
    detected_name varchar(255) null,
    timestamp     timestamp    null
);

create table ass3.known_faces
(
    id        int auto_increment
        primary key,
    name      varchar(255) null,
    encoding  text         null,
    timestamp timestamp    null
);

