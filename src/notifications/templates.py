TEMPLATES = {
    # Module 1 — Scrape Run Complete
    "scrape_run_complete": """━━━━━━━━━━━━━━━━━━━━━━━━━━━
:mag: *Scrape Run Complete*
━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Run ID:* {run_id}
*Duration:* {duration_minutes}m {duration_seconds}s
*Completed:* {completed_at}

*Results:*
- Jobs scraped: {jobs_scraped}
- Passed ICP filter: {jobs_passed_icp}
- Contacts extracted: {contacts_extracted}
- Pushed to outreach: {pushed_to_outreach}
- Errors: {error_count}

*By Funding Stage:*
- Series A: {count_series_a}
- Series B: {count_series_b}
- Series C: {count_series_c}
- Series D+: {count_series_d_plus}

*By Role Category:*
- Sales Leadership: {count_sales}
- Marketing: {count_marketing}
- GTM / RevOps: {count_gtm}
- CS Leadership: {count_cs}
- SDR/BDR: {count_sdr}

*Top Boards:*
{top_boards_list}
━━━━━━━━━━━━━━━━━━━━━━━━━━━""",

    # Scrape Board Complete (single board)
    "scrape_board_complete": """:mag: *Scrape Complete — {board_name}*
Run ID: {run_id}
Jobs found: {jobs_found} | New: {jobs_new}""",

    # Scrape Error Alert
    "scrape_board_error": """:warning: *Scraper Alert — High Error Rate*
Board: *{board_name}*
Error rate: *{error_rate_pct}%* ({errors} / {attempts} requests)
Run ID: {run_id}
Last error: `{last_error_message}`
Action needed: Check proxy, board structure, or rate limiting.""",

    # Module 2 — Outreach Launched
    "outreach_launched": """:rocket: *Outreach Launched*
*{first_name} {last_name}* — {title}
*Company:* {company} ({funding_stage})
*ICP Score:* {icp_score}/100 | *Category:* {gtm_role_category}
*Source:* {source_board}
Channels launched:
:email: Instantly -> Campaign: {instantly_campaign_name}
:link: Lemlist -> Campaign: {lemlist_campaign_name}
:telephone_receiver: Call reminder: {call_reminder_date}
:card_index: CRM: {crm_deal_link}""",

    # Module 3 — Positive Reply
    "reply_positive": """━━━━━━━━━━━━━━━━━━━━━━━━━━━
:large_green_circle: *Positive Reply*
━━━━━━━━━━━━━━━━━━━━━━━━━━━
*{first_name} {last_name}* {title} @ *{company}*
Funding: {funding_stage} | ICP Score: {icp_score}/100
Category: {gtm_role_category}

*Their reply:*
> {reply_excerpt}

*Actions taken automatically:*
:white_check_mark: Booking link sent to {prospect_email}
:double_vertical_bar: Instantly campaign paused
:double_vertical_bar: Lemlist campaign paused
:clipboard: CRM updated -> _{crm_deal_stage}_

*Assigned to:* <@{recruiter_slack_id}>
*CRM Deal:* {crm_deal_link}
*LinkedIn:* {linkedin_url}
━━━━━━━━━━━━━━━━━━━━━━━━━━━""",

    # Objection Reply
    "reply_objection": """:large_yellow_circle: *Objection Reply — Review Needed*
*{first_name} {last_name}* — {title} @ *{company}*
Funding: {funding_stage} | ICP Score: {icp_score}/100

*Their reply:*
> {reply_excerpt}

*AI confidence:* {confidence_pct}%
*Campaigns paused* — no auto-response sent.
<@{recruiter_slack_id}> review and decide how to respond.
*CRM:* {crm_deal_link}""",

    # OOO with Date
    "reply_ooo_with_date": """:large_blue_circle: *Out of Office*
*{first_name} {last_name}* @ *{company}*
Returns: *{return_date}*
Campaign paused automatically.
:arrow_forward: Resume scheduled for: *{resume_date}*
:telephone_receiver: Call reminder rescheduled to: *{new_call_reminder_date}*
_No action needed._""",

    # OOO without Date
    "reply_ooo_no_date": """:large_blue_circle: *Out of Office — No Return Date Detected*
*{first_name} {last_name}* @ *{company}*
Campaign paused. No return date found in message.
<@{recruiter_slack_id}> — manually set resume date if needed.
*CRM:* {crm_deal_link}""",

    # Unsubscribe
    "reply_unsubscribe": """:red_circle: *Unsubscribe Request — All Channels Suppressed*
*{first_name} {last_name}* @ *{company}*
Email: {prospect_email}

*Actions completed:*
:no_entry: Instantly campaign paused + email suppressed
:no_entry: Lemlist campaign paused + email suppressed
:clipboard: CRM logged: _"Unsubscribe request. All campaigns paused."_
_No further outreach will be sent. No action needed._""",

    # Unknown / Unclassified Reply
    "reply_other": """:question: *Reply Needs Human Review*
*{first_name} {last_name}* @ *{company}*
AI category: `other` | Confidence: {confidence_pct}%

*Their reply:*
> {reply_excerpt}

<@{recruiter_slack_id}> — please review and take manual action.
*CRM:* {crm_deal_link}""",

    # Consecutive Outreach Failures
    "outreach_failure": """:rotating_light: *Outreach Failures — Intervention Required*
*{failure_count}* consecutive prospects failed at step: *{failed_step}*
Last error: `{last_error}`
Last prospect: {last_prospect_name} @ {last_prospect_company}
Time: {timestamp}
Check API keys, campaign status, and rate limits for {failed_step} before next scrape cycle.""",

    # Booking Email Reply
    "booking_email": """Subject: Re: {original_subject}

Hi {first_name},

{personalized_opener}

I'd love to find 20 minutes to connect — feel free to grab time directly on my calendar here:
{booking_link}

Looking forward to it,
{sender_name}
{sender_title}""",
}
