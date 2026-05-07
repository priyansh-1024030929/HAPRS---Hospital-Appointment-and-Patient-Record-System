create database if not exists haprs;
use haprs;

create table if not exists Patient(
	pid int auto_increment primary key,
	firstName varchar(50) not null,
	lastName varchar(50) not null,
	dob date,
	gender varchar(10) check (gender in ('Male','Female','Other')),
	phone varchar(15),
	email varchar(100),
	address varchar(255),
	bloodgrp varchar(5) check (bloodgrp in ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
	insuranceID varchar(50) unique,
	registrationDate date
);

create table if not exists Specialization(
	sid int auto_increment primary key,
	specializationName varchar(100)
);

create table if not exists Doctor(
	did int auto_increment primary key,
	name varchar(100) not null,
	sid int null,
	phone varchar(15),
	email varchar(100),
	room int unique,
	availability_schedule varchar(255),
	constraint fk_doc_sid foreign key (sid) references Specialization(sid) on delete set null
);

create table if not exists Appointment(
	aid int auto_increment primary key,
	pid int,
	did int null,
	aptDate date default (current_date),
	aptTime time default (current_time),
	status varchar(25) check (status in ('Not Completed','Completed','Cancelled')),
	reasonForVisit text,
	constraint fk_apt_pid foreign key (pid) references Patient(pid) on delete cascade,
	constraint fk_apt_did foreign key (did) references Doctor(did) on delete set null
);

create table if not exists MedicalRecord(
	rid int auto_increment primary key,
	pid int,
	did int null,
	visitDate date,
	diagnosis text,
	prescription text,
	testRecommended text,
	notes text,
	constraint fk_rec_pid foreign key (pid) references Patient(pid) on delete cascade,
	constraint fk_rec_did foreign key (did) references Doctor(did) on delete set null
);

create table if not exists Billing(
	bid int auto_increment primary key,
	pid int,
	aid int,
	consultationFee decimal(10,2),
	testCharges decimal(10,2),
	pharmaCharges decimal(10,2),
	totalAmount decimal(10,2),
	paymentStatus varchar(25) check (paymentStatus in ('Paid','Unpaid','Pending')) default 'Pending',
	paymentMode varchar(25) check (paymentMode in ('Cash','Card','Insurance')),
	constraint fk_bill_pid foreign key (pid) references Patient(pid) on delete cascade,
	constraint fk_bill_aid foreign key (aid) references Appointment(aid) on delete cascade
);

-- ===================== ROUTINES =====================


delimiter $$

-- Trigger: prevent double booking

create trigger prevent_double_booking_insert
before insert on appointment
for each row
begin
    if new.did is not null and exists (
        select 1 from appointment
        where did = new.did
        and aptdate = new.aptdate
        and apttime = new.apttime
    ) then
        signal sqlstate '45000'
        set message_text = 'doctor already has an appointment at this time';
    end if;
end$$

-- Safe appointment booking

create procedure book_appointment_safe(
    in p_pid int,
    in p_did int,
    in p_date date,
    in p_time time,
	in p_status varchar(25),
    in p_reason text
)
begin
    declare conflict_count int default 0;
    declare doctor_exists int default 0;

    if p_did is not null then
        select count(*) into doctor_exists
        from doctor
        where did = p_did;

        if doctor_exists = 0 then
            signal sqlstate '45000'
            set message_text = 'doctor does not exist';
        end if;
    end if;

    if p_did is not null then
        select count(*) into conflict_count
        from appointment
        where did = p_did
        and aptdate = p_date
        and apttime = p_time;

        if conflict_count > 0 then
            signal sqlstate '45000'
            set message_text = 'time slot already booked for this doctor';
        end if;
    end if;

	if p_status is null or p_status = '' then
        set p_status = 'not completed';
    end if;

    insert into appointment(pid, did, aptdate, apttime, status, reasonforvisit)
    values (p_pid, p_did, p_date, p_time, p_status, p_reason);

end$$

-- Function: total

create function calc_total(
    f decimal(10,2),
    t decimal(10,2),
    p decimal(10,2)
)
returns decimal(10,2)
deterministic
begin
    return ifnull(f,0) + ifnull(t,0) + ifnull(p,0);
end$$

-- Safe billing

create procedure create_bill_safe(
    in p_pid int,
    in p_aid int,
    in p_consult decimal(10,2),
    in p_test decimal(10,2),
    in p_pharma decimal(10,2),
    in p_status varchar(25),
    in p_mode varchar(25)
)
begin
    declare apt_count int default 0;
    declare correct_patient int default 0;

    select count(*) into apt_count
    from appointment
    where aid = p_aid;

    if apt_count = 0 then
        signal sqlstate '45000'
        set message_text = 'appointment does not exist';
    end if;

    select count(*) into correct_patient
    from appointment
    where aid = p_aid and pid = p_pid;

    if correct_patient = 0 then
        signal sqlstate '45000'
        set message_text = 'patient does not match appointment';
    end if;

    if p_status is null or p_status = '' then
        set p_status = 'pending';
    end if;

    insert into billing(pid, aid, consultationfee, testcharges, pharmacharges, totalamount, paymentstatus, paymentmode)
    values (
        p_pid,
        p_aid,
        p_consult,
        p_test,
        p_pharma,
        calc_total(p_consult, p_test, p_pharma),
        p_status,
        p_mode
    );
end$$

-- Billing triggers

create trigger billing_total_before_insert
before insert on billing
for each row
begin
    set new.totalamount = ifnull(new.consultationfee,0)
                        + ifnull(new.testcharges,0)
                        + ifnull(new.pharmacharges,0);
end$$

create trigger prevent_duplicate_bill
before insert on billing
for each row
begin
    if exists (
        select 1 from billing where aid = new.aid
    ) then
        signal sqlstate '45000'
        set message_text = 'bill already exists for this appointment';
    end if;
end$$

create trigger validate_payment_mode
before insert on billing
for each row
begin
    if new.paymentmode not in ('cash','card','insurance') then
        signal sqlstate '45000'
        set message_text = 'invalid payment mode';
    end if;
end$$

create trigger billing_after_update
after update on billing
for each row
begin
    if new.paymentstatus = 'paid' then
        update appointment
        set status = 'completed'
        where aid = new.aid;
    end if;
end$$

-- Views

create view appointment_full_view as
select 
    a.aid,
    a.aptdate,
    a.apttime,
    a.status,
    a.reasonforvisit,

    p.pid,
    concat(p.firstname, ' ', p.lastname) as patient_name,
    p.phone as patient_phone,

    d.did,
    d.name as doctor_name,
    s.specializationname

from appointment a
join patient p on a.pid = p.pid
left join doctor d on a.did = d.did
left join specialization s on d.sid = s.sid;

create view billing_full_view as
select 
    b.bid,
    b.totalamount,
    b.paymentstatus,
    b.paymentmode,

    p.pid,
    concat(p.firstname, ' ', p.lastname) as patient_name,

    a.aid,
    a.aptdate,
    a.apttime

from billing b
join patient p on b.pid = p.pid
join appointment a on b.aid = a.aid;

create view doctor_workload_view as
select 
    d.did,
    d.name as doctor_name,
    s.specializationname,

    count(a.aid) as total_appointments

from doctor d
left join appointment a on d.did = a.did
left join specialization s on d.sid = s.sid

group by d.did, d.name, s.specializationname;

create view daily_appointment_summary as
select 
    aptdate,
    count(*) as total_appointments,
    sum(case when status = 'completed' then 1 else 0 end) as completed,
    sum(case when status = 'not completed' then 1 else 0 end) as pending
from appointment
group by aptdate;

create view patient_history_view as
select 
    p.pid,
    concat(p.firstname, ' ', p.lastname) as patient_name,

    a.aid,
    a.aptdate,
    a.status,

    d.name as doctor_name,
    s.specializationname

from patient p
left join appointment a on p.pid = a.pid
left join doctor d on a.did = d.did
left join specialization s on d.sid = s.sid;

create view revenue_summary_view as
select 
    date(a.aptdate) as date,
    sum(b.totalamount) as total_revenue,
    count(b.bid) as total_bills
from billing b
join appointment a on b.aid = a.aid
where b.paymentstatus = 'paid'
group by date(a.aptdate);

-- Book and bill

create procedure book_and_bill(
    in p_pid int,
    in p_did int,
    in p_date date,
    in p_time time,
    in p_status varchar(25),
    in p_reason text,

    in p_consult decimal(10,2),
    in p_test decimal(10,2),
    in p_pharma decimal(10,2),
    in p_paymentstatus varchar(25),
    in p_paymentmode varchar(25)
)
begin
    declare new_aid int;

    declare exit handler for sqlexception
    begin
        rollback;
    end;

    start transaction;

    -- step 1: book appointment
    call book_appointment_safe(
        p_pid, p_did, p_date, p_time, p_status, p_reason
    );

    set new_aid = last_insert_id();

    -- step 2: create bill using existing procedure
    call create_bill_safe(
        p_pid,
        new_aid,
        p_consult,
        p_test,
        p_pharma,
        p_paymentstatus,
        p_paymentmode
    );

    commit;
end$$

delimiter ;