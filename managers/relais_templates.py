"""
VDE Messwand - Relais-Konfigurationsvorlagen
Vordefinierte Templates für schnelle Einrichtung
"""

def get_available_templates():
    """
    Gibt verfügbare Vorlagen zurück

    Returns:
        Liste von Template-Dictionaries
    """
    return [
        {
            'id': 'cee_3phase',
            'name': 'CEE 3-Phasen Steckdose',
            'description': 'Standard CEE 16A Steckdose mit 3 Phasen gruppiert',
            'relais_count': 5
        },
        {
            'id': 'herd_4wire',
            'name': 'Herdanschluss 4-adrig',
            'description': 'Herdanschlussdose mit L1, L2, L3, N gruppiert',
            'relais_count': 4
        },
        {
            'id': 'wallbox_3phase',
            'name': 'Wallbox 3-Phasen',
            'description': 'E-Auto Ladestation mit 3 Phasen und PE',
            'relais_count': 4
        },
        {
            'id': 'bad_rcbo',
            'name': 'Bad mit RCBO',
            'description': 'Badezimmer-Stromkreis mit RCBO und typischen Fehlern',
            'relais_count': 8
        },
        {
            'id': 'standard_circuit',
            'name': 'Standard Stromkreis',
            'description': 'Einfacher Stromkreis mit L, N, PE',
            'relais_count': 3
        }
    ]


def get_template_config(template_id):
    """
    Gibt die Relais-Konfiguration für eine Vorlage zurück

    Args:
        template_id: ID der Vorlage

    Returns:
        Dictionary mit Relais-Konfigurationen oder None
    """
    templates = {
        'cee_3phase': {
            0: {'group_number': 1, 'name': 'CEE L1', 'category': 'RISO', 'stromkreis': 'L1'},
            1: {'group_number': 1, 'name': 'CEE L2', 'category': 'RISO', 'stromkreis': 'L2'},
            2: {'group_number': 1, 'name': 'CEE L3', 'category': 'RISO', 'stromkreis': 'L3'},
            3: {'group_number': 0, 'name': 'CEE N', 'category': 'Zi', 'stromkreis': 'N'},
            4: {'group_number': 0, 'name': 'CEE PE', 'category': 'Zi', 'stromkreis': 'PE'}
        },

        'herd_4wire': {
            10: {'group_number': 2, 'name': 'Herd L1', 'category': 'RISO', 'stromkreis': 'L1'},
            11: {'group_number': 2, 'name': 'Herd L2', 'category': 'RISO', 'stromkreis': 'L2'},
            12: {'group_number': 2, 'name': 'Herd L3', 'category': 'RISO', 'stromkreis': 'L3'},
            13: {'group_number': 2, 'name': 'Herd N', 'category': 'Zi', 'stromkreis': 'N'}
        },

        'wallbox_3phase': {
            50: {'group_number': 3, 'name': 'Wallbox L1', 'category': 'RISO', 'stromkreis': 'L1'},
            51: {'group_number': 3, 'name': 'Wallbox L2', 'category': 'RISO', 'stromkreis': 'L2'},
            52: {'group_number': 3, 'name': 'Wallbox L3', 'category': 'RISO', 'stromkreis': 'L3'},
            53: {'group_number': 0, 'name': 'Wallbox PE', 'category': 'Zi', 'stromkreis': 'PE'}
        },

        'bad_rcbo': {
            40: {'group_number': 4, 'name': 'Bad L', 'category': 'RCD', 'stromkreis': 'L1'},
            41: {'group_number': 4, 'name': 'Bad N', 'category': 'RCD', 'stromkreis': 'N'},
            42: {'group_number': 0, 'name': 'Bad PE normal', 'category': 'Zi', 'stromkreis': 'PE'},
            43: {'group_number': 0, 'name': 'Bad PE Fehler', 'category': 'Zi', 'stromkreis': 'PE'},
            44: {'group_number': 0, 'name': 'Bad Steckdose', 'category': 'RCD', 'stromkreis': 'L1'},
            45: {'group_number': 0, 'name': 'Bad Lampe', 'category': 'RCD', 'stromkreis': 'L1'},
            46: {'group_number': 0, 'name': 'Bad N-Fehler', 'category': 'RCD', 'stromkreis': 'N'},
            47: {'group_number': 0, 'name': 'Bad RCBO Test', 'category': 'RCD', 'stromkreis': 'L1'}
        },

        'standard_circuit': {
            20: {'group_number': 5, 'name': 'Stromkreis L', 'category': 'Zs', 'stromkreis': 'L1'},
            21: {'group_number': 5, 'name': 'Stromkreis N', 'category': 'Zs', 'stromkreis': 'N'},
            22: {'group_number': 0, 'name': 'Stromkreis PE', 'category': 'Zi', 'stromkreis': 'PE'}
        }
    }

    return templates.get(template_id)


def apply_template(template_id, start_relay=None, group_offset=0):
    """
    Wendet eine Vorlage an und gibt die Konfiguration zurück

    Args:
        template_id: ID der Vorlage
        start_relay: Optional: Ab welchem Relais beginnen (verschiebt alle Relais)
        group_offset: Optional: Offset für Gruppen-Nummern (verhindert Überschneidungen)

    Returns:
        Dictionary mit angepasster Relais-Konfiguration oder None
    """
    template_config = get_template_config(template_id)

    if not template_config:
        return None

    # Wenn start_relay angegeben, verschiebe alle Relais
    if start_relay is not None:
        relay_numbers = sorted(template_config.keys())
        offset = start_relay - relay_numbers[0]

        new_config = {}
        for old_num, config in template_config.items():
            new_num = old_num + offset
            if 0 <= new_num <= 63:  # Nur gültige Relais-Nummern
                new_config[new_num] = config.copy()

                # Gruppen-Offset anwenden
                if group_offset > 0 and new_config[new_num]['group_number'] > 0:
                    new_config[new_num]['group_number'] += group_offset

        return new_config

    # Gruppen-Offset anwenden
    if group_offset > 0:
        new_config = {}
        for relay_num, config in template_config.items():
            new_config[relay_num] = config.copy()
            if new_config[relay_num]['group_number'] > 0:
                new_config[relay_num]['group_number'] += group_offset
        return new_config

    return template_config


def get_template_info(template_id):
    """
    Gibt detaillierte Informationen über eine Vorlage

    Args:
        template_id: ID der Vorlage

    Returns:
        Dictionary mit Template-Info
    """
    templates = get_available_templates()

    for template in templates:
        if template['id'] == template_id:
            config = get_template_config(template_id)

            # Analysiere Template
            relay_numbers = sorted(config.keys()) if config else []
            groups = set()
            categories = set()

            if config:
                for relay_config in config.values():
                    if relay_config['group_number'] > 0:
                        groups.add(relay_config['group_number'])
                    if relay_config['category']:
                        categories.add(relay_config['category'])

            return {
                **template,
                'relay_range': f"{relay_numbers[0]}-{relay_numbers[-1]}" if relay_numbers else "",
                'group_count': len(groups),
                'categories': list(categories),
                'config_preview': config
            }

    return None
