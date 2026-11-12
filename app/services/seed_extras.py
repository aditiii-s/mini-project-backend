"""Seeds announcements, knowledge base articles and starter notifications."""
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Announcement, Complaint, Employee, KbArticle, Notification

NOW = datetime.now()

ANNOUNCEMENTS = [
    {
        "title": "Scheduled maintenance: billing servers",
        "body": (
            "The revenue billing servers will be unavailable on Sunday from 02:00 to 05:00 for "
            "quarterly patching. Please close the application before leaving on Saturday."
        ),
        "kind": "Maintenance",
        "days_ago": 2,
    },
    {
        "title": "Head Office link upgrade completed",
        "body": (
            "The Patna head office internet link has been upgraded. If the VPN still drops after "
            "reconnecting once, please raise a Network complaint."
        ),
        "kind": "Update",
        "days_ago": 5,
    },
    {
        "title": "Email storage cleanup",
        "body": (
            "Mailboxes above 90 percent of quota will stop receiving mail. Archive old "
            "attachments or raise an Other complaint to request extra storage."
        ),
        "kind": "Notice",
        "days_ago": 9,
    },
]

KB_ARTICLES = [
    {
        "slug": "printer-not-printing",
        "category": "Printer",
        "question": "The shared printer is not printing anything",
        "summary": "Most print failures are a paused queue or the wrong default printer.",
        "steps": (
            "Check the printer is powered on and shows Ready on its panel.\n"
            "Open Settings, then Bluetooth and devices, then Printers and scanners.\n"
            "Select the printer and choose Open print queue.\n"
            "If the queue says Paused, clear the pause and cancel any stuck jobs.\n"
            "Set the correct printer as default and print a test page.\n"
            "If it still fails, raise a Printer complaint with the printer name and section."
        ),
    },
    {
        "slug": "paper-jam",
        "category": "Printer",
        "question": "How do I clear a paper jam safely?",
        "summary": "Pull jammed paper in the direction of travel, never backwards.",
        "steps": (
            "Switch the printer off and open the rear access door.\n"
            "Pull the jammed sheet slowly in the direction the paper was feeding.\n"
            "Remove any torn pieces, because they cause repeat jams.\n"
            "Fan the paper stack before reloading and do not overfill the tray.\n"
            "Power on and print a test page.\n"
            "If it jams every few pages the pickup roller may be worn, so raise a complaint."
        ),
    },
    {
        "slug": "vpn-disconnects",
        "category": "Network",
        "question": "The VPN keeps disconnecting",
        "summary": "Usually an unstable link or an expired VPN profile.",
        "steps": (
            "Check whether other sites load while the VPN is down.\n"
            "Disconnect, wait ten seconds, and reconnect once.\n"
            "Prefer a LAN cable over Wi-Fi for long sessions.\n"
            "Restart the VPN client completely rather than reconnecting repeatedly.\n"
            "If it still drops at regular intervals, raise a Network complaint and say how often."
        ),
    },
    {
        "slug": "no-internet",
        "category": "Network",
        "question": "My desktop has no internet access",
        "summary": "Check the cable and the network icon before raising a ticket.",
        "steps": (
            "Confirm the LAN cable is firmly seated at both ends and the port light blinks.\n"
            "Check whether colleagues in the same section are also affected.\n"
            "Restart the desktop once.\n"
            "If only your machine is affected, note the port number and raise a Network complaint."
        ),
    },
    {
        "slug": "billing-app-slow",
        "category": "Software",
        "question": "The billing application is very slow",
        "summary": "Peak hour slowness is common between 11:00 and 13:00.",
        "steps": (
            "Close other heavy applications and browser tabs.\n"
            "Sign out of the billing application and sign in again.\n"
            "Clear the application cache from Tools, then Options, if available.\n"
            "Note the exact screens that are slow and the time of day.\n"
            "Raise a Software complaint with those details so the IT Cell can check server logs."
        ),
    },
    {
        "slug": "forgot-password",
        "category": "Software",
        "question": "I have forgotten my application password",
        "summary": "Passwords are reset by the IT Cell after identity verification.",
        "steps": (
            "Try your most recent password once, because repeated failures may lock the account.\n"
            "Raise an Other complaint stating which application is affected.\n"
            "Mention your Employee ID and section so the IT Cell can verify your identity.\n"
            "You will receive a temporary password, which you should change at first sign in."
        ),
    },
    {
        "slug": "ups-beeping",
        "category": "Hardware",
        "question": "My UPS beeps continuously",
        "summary": "Continuous beeping normally means the battery is at the end of its life.",
        "steps": (
            "Check whether mains power is present at the wall socket.\n"
            "Disconnect any printer or heater plugged into the UPS, because they overload it.\n"
            "Note how long the UPS holds the load after a power cut.\n"
            "If backup lasts under five minutes, raise a Hardware complaint with the asset tag."
        ),
    },
    {
        "slug": "monitor-no-display",
        "category": "Hardware",
        "question": "My monitor shows no display",
        "summary": "Usually a loose cable or the wrong input source.",
        "steps": (
            "Confirm the monitor power light is on.\n"
            "Reseat the VGA, HDMI or DisplayPort cable at both ends.\n"
            "Press the monitor Source or Input button to cycle to the correct input.\n"
            "Try the monitor on another machine if one is available.\n"
            "If it stays blank, raise a Hardware complaint with the asset tag."
        ),
    },
    {
        "slug": "request-vs-complaint",
        "category": "Other",
        "question": "Should I raise a complaint or a service request?",
        "summary": "Complaints are for things that are broken, service requests for new items or access.",
        "steps": (
            "Something that used to work has stopped working, so raise a complaint.\n"
            "You need new hardware, a software installation, network access or an email account, "
            "so raise a service request.\n"
            "Service requests go through approval, while complaints are assigned to an engineer."
        ),
    },
]

STARTER_NOTIFICATIONS = [
    (
        "IT-2026-0121",
        "Resolution",
        "IT-2026-0121 is now Resolved",
        "Pickup roller replaced, test print successful.",
        15,
    ),
    (
        "IT-2026-0134",
        "Assignment",
        "IT-2026-0134 assigned to an engineer",
        "Anjali Mishra - Software is now handling this complaint.",
        7,
    ),
    (
        "IT-2026-0134",
        "Status",
        "IT-2026-0134 is now In Progress",
        "Application logs collected, database query tuning under way.",
        5,
    ),
]


def seed_extras() -> None:
    db = SessionLocal()
    try:
        if db.query(Announcement).count() == 0:
            for item in ANNOUNCEMENTS:
                db.add(
                    Announcement(
                        title=item["title"],
                        body=item["body"],
                        kind=item["kind"],
                        active=True,
                        created_at=NOW - timedelta(days=item["days_ago"]),
                    )
                )

        if db.query(KbArticle).count() == 0:
            for item in KB_ARTICLES:
                db.add(KbArticle(**item))

        employee = db.query(Employee).filter(Employee.employee_id == "EMP1024").first()
        if employee:
            existing = (
                db.query(Notification).filter(Notification.employee_id == employee.id).count()
            )
            if existing == 0:
                tickets = {
                    c.ticket_id
                    for c in db.query(Complaint)
                    .filter(Complaint.employee_id == employee.id)
                    .all()
                }
                for ticket, kind, title, body, days in STARTER_NOTIFICATIONS:
                    if ticket in tickets:
                        db.add(
                            Notification(
                                employee_id=employee.id,
                                title=title,
                                body=body,
                                kind=kind,
                                ticket_id=ticket,
                                is_read=False,
                                created_at=NOW - timedelta(days=days),
                            )
                        )

        db.commit()
        print("Extras seeded: announcements, knowledge base articles and notifications.")
    finally:
        db.close()
