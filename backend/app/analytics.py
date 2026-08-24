from sqlalchemy.orm import Session

from .db.models import TelemetryRecord


def get_latest_insights(db: Session):
    record = (
        db.query(TelemetryRecord)
        .filter(
            TelemetryRecord.device_id == "esp32-01"
        )
        .order_by(
            TelemetryRecord.timestamp.desc()
        )
        .first()
    )

    if record is None:
        return {
            "status": "no_data",
            "insights": []
        }

    insights = []

    # Occupancy / motion insight
    if record.pir1_motion or record.pir2_motion:
        insights.append(
            "Motion detected in the campus zones."
        )
    else:
        insights.append(
            "No motion detected in the monitored zones."
        )

    # Temperature / cooling insight
    if record.temperature_c >= 35:
        if record.fan_state:
            insights.append(
                "High temperature detected and fan is running."
            )
        else:
            insights.append(
                "High temperature detected while fan is OFF."
            )
    else:
        insights.append(
            "Temperature is within the current normal range."
        )

    # Lighting insight
    if (
        record.pir1_motion
        and not record.bulb1_state
    ):
        insights.append(
            "Motion detected in Zone 1 while the bulb is OFF."
        )

    if (
        record.pir2_motion
        and not record.bulb2_state
    ):
        insights.append(
            "Motion detected in Zone 2 while the bulb is OFF."
        )

    # Energy insight
    if (
        record.current_indication is not None
        and record.current_indication > 0.5
    ):
        insights.append(
            "Current consumption is relatively high."
        )

    return {
        "status": "ok",
        "device_id": record.device_id,
        "timestamp": record.timestamp,
        "insights": insights
    }


def get_historical_insights(db: Session):
    records = (
        db.query(TelemetryRecord)
        .filter(
            TelemetryRecord.device_id == "esp32-01",
            TelemetryRecord.temperature_c > 0,
            TelemetryRecord.humidity_percent > 0
        )
        .order_by(
            TelemetryRecord.timestamp.asc()
        )
        .all()
    )

    if not records:
        return {
            "status": "no_data",
            "device_id": "esp32-01",
            "high_temperature_episodes": [],
            "total_high_temperature_episodes": 0
        }

    episode_indexes = []
    current_episode = []

    for index, record in enumerate(records):
        if record.temperature_c < 40:
            if current_episode:
                episode_indexes.append(current_episode)
                current_episode = []

            continue

        if (
            current_episode
            and (
                record.timestamp -
                records[current_episode[-1]].timestamp
            ).total_seconds() > 15
        ):
            episode_indexes.append(current_episode)
            current_episode = []

        current_episode.append(index)

    if current_episode:
        episode_indexes.append(current_episode)

    high_temperature_episodes = []

    for episode_number, indexes in enumerate(episode_indexes):
        episode_records = [records[index] for index in indexes]
        peak_index = max(
            indexes,
            key=lambda index: records[index].temperature_c
        )
        peak_record = records[peak_index]
        next_episode_start = (
            episode_indexes[episode_number + 1][0]
            if episode_number + 1 < len(episode_indexes)
            else len(records)
        )
        fan_remained_on = bool(peak_record.fan_state)
        cooling_response_observed = False

        for record in records[peak_index + 1:next_episode_start]:
            if not record.fan_state:
                fan_remained_on = False
                break

            if fan_remained_on and record.temperature_c < peak_record.temperature_c:
                cooling_response_observed = True
                break

        high_temperature_episodes.append(
            {
                "start_timestamp": episode_records[0].timestamp.isoformat(),
                "end_timestamp": episode_records[-1].timestamp.isoformat(),
                "peak_temperature": peak_record.temperature_c,
                "sample_count": len(episode_records),
                "cooling_response_observed": cooling_response_observed
            }
        )

    return {
        "status": "ok",
        "device_id": "esp32-01",
        "high_temperature_episodes": high_temperature_episodes,
        "total_high_temperature_episodes": len(high_temperature_episodes)
    }


def get_anomaly_summary(db: Session):
    records = (
        db.query(TelemetryRecord)
        .filter(
            TelemetryRecord.device_id == "esp32-01"
        )
        .order_by(
            TelemetryRecord.timestamp.asc()
        )
        .all()
    )

    if not records:
        return {
            "status": "no_data",
            "device_id": "esp32-01",
            "total_high_temperature_episodes": 0,
            "high_temperature_episodes_with_cooling_response": 0,
            "potential_cooling_anomalies": 0,
            "total_current_spike_warnings": 0,
            "sustained_unexplained_current_episodes": 0,
            "current_anomalies": []
        }

    environmental_records = [
        record
        for record in records
        if (
            record.temperature_c > 0
            and record.humidity_percent > 0
        )
    ]
    temperature_episodes = []
    current_temperature_episode = []

    for index, record in enumerate(environmental_records):
        if record.temperature_c < 40:
            if current_temperature_episode:
                temperature_episodes.append(
                    current_temperature_episode
                )
                current_temperature_episode = []

            continue

        if (
            current_temperature_episode
            and (
                record.timestamp -
                environmental_records[
                    current_temperature_episode[-1]
                ].timestamp
            ).total_seconds() > 15
        ):
            temperature_episodes.append(
                current_temperature_episode
            )
            current_temperature_episode = []

        current_temperature_episode.append(index)

    if current_temperature_episode:
        temperature_episodes.append(current_temperature_episode)

    cooling_responses = 0

    for episode_number, indexes in enumerate(temperature_episodes):
        peak_index = max(
            indexes,
            key=lambda index: environmental_records[
                index
            ].temperature_c
        )
        peak_record = environmental_records[peak_index]
        next_episode_start = (
            temperature_episodes[episode_number + 1][0]
            if episode_number + 1 < len(temperature_episodes)
            else len(environmental_records)
        )
        fan_remained_on = bool(peak_record.fan_state)
        cooling_response_observed = False

        for record in environmental_records[
            peak_index + 1:next_episode_start
        ]:
            if not record.fan_state:
                fan_remained_on = False
                break

            if (
                fan_remained_on
                and record.temperature_c < peak_record.temperature_c
            ):
                cooling_response_observed = True
                break

        if cooling_response_observed:
            cooling_responses += 1

    elevated_current_runs = []
    current_elevated_run = []

    for index, record in enumerate(records):
        is_elevated_with_devices_off = (
            record.current_indication is not None
            and record.current_indication >= 1.0
            and not record.fan_state
            and not record.bulb1_state
            and not record.bulb2_state
        )

        if not is_elevated_with_devices_off:
            if current_elevated_run:
                elevated_current_runs.append(current_elevated_run)
                current_elevated_run = []

            continue

        if (
            current_elevated_run
            and (
                record.timestamp -
                records[current_elevated_run[-1]].timestamp
            ).total_seconds() > 30
        ):
            elevated_current_runs.append(current_elevated_run)
            current_elevated_run = []

        current_elevated_run.append(index)

    if current_elevated_run:
        elevated_current_runs.append(current_elevated_run)

    current_spike_warnings = 0
    current_anomalies = []

    for indexes in elevated_current_runs:
        if len(indexes) == 1:
            current_spike_warnings += 1
            continue

        episode_records = [records[index] for index in indexes]
        peak_current = max(
            record.current_indication
            for record in episode_records
        )

        current_anomalies.append(
            {
                "start_timestamp": episode_records[0].timestamp.isoformat(),
                "end_timestamp": episode_records[-1].timestamp.isoformat(),
                "peak_current": peak_current,
                "sample_count": len(episode_records)
            }
        )

    total_temperature_episodes = len(temperature_episodes)

    return {
        "status": "ok",
        "device_id": "esp32-01",
        "total_high_temperature_episodes": total_temperature_episodes,
        "high_temperature_episodes_with_cooling_response": cooling_responses,
        "potential_cooling_anomalies": (
            total_temperature_episodes - cooling_responses
        ),
        "total_current_spike_warnings": current_spike_warnings,
        "sustained_unexplained_current_episodes": len(current_anomalies),
        "current_anomalies": current_anomalies
    }
