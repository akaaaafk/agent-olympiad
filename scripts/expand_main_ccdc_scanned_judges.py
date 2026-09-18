"""Enable five original-page-reviewed scanned CCDC packets for written planning."""
from expand_main_ccdc_judges import main

SCANNED_CASES = {
    2015: (27, 22, 'Stark Energy',
        'Electrical utility: preserve power continuity, corporate/control-center/plant segmentation, '
        'plant access only through the control center, public NAT service addresses, rollback and protected monitoring devices.'),
    2016: (26, 21, 'ODIN',
        'Aerospace and defense contractor: preserve corporate, Cypress Creek and confidential-data segmentation. '
        'Confidential data is reached through Cypress Creek; preserve file integrity, availability and specified scoring-system access.'),
    2017: (27, 21, 'Dwarven Hammer',
        'Comic-book and collectible retail: preserve all three retail networks and DOS-based KeyHut Point of Sale registers and servers. '
        'Maintain the specifically restricted SMB access and public critical services. '
        'The original map displays N7 branding while the scenario letter names Dwarven Hammer; '
        'state this source discrepancy and use the letter for business context without inventing a corrected map.'),
    2018: (27, 21, 'Volitech',
        'Biotechnology: protect headquarters and remote R&D services and data, preserve authorized remote access, '
        'legacy application compatibility, assigned service addresses, DNS/proxy requirements and CCSClient.'),
    2019: (26, 20, 'Cryovine',
        'Agriculture and cryogenic seed storage: preserve headquarters, Tech Ops and Farm Lab dependencies, '
        'authorized farm HTTP/RDP/SSH access, ERP, required DNS/proxy behavior and CCSClient. '
        'Do not treat an infrastructure hosting boundary as authority to alter unprovided hosting systems.'),
}


if __name__ == '__main__':
    main(SCANNED_CASES, 'main_ccdc_scanned_expansion_20260917.json', scanned=True)
