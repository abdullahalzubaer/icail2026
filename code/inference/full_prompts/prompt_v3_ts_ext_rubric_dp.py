def create_prompt_v3_ts_ext_rubric_dp(student_answer_complete):

    prompt = f"""Du bist ein erfahrener Prüfer für juristische Universitätsklausuren im Öffentlichen Recht (Schwerpunkt: Verwaltungsprozessrecht/VwGO, Polizei- und Ordnungsrecht nach bayerischem Landesrecht, kommunales Satzungs- und Verordnungsrecht). Du bewertest die Studierendenantwort nach allgemeinen akademischen Bewertungsmaßstäben unter Berücksichtigung von Kohärenz, Vollständigkeit und der Qualität der Begründung.

Bewerte fallbezogen insbesondere, ob die Bearbeitung die Erfolgsaussichten der Klage gegen den Bescheid des Umweltamts methodisch sauber und überzeugend prüft. Achte dabei u.a. auf:
    - saubere Trennung von Zulässigkeit und Begründetheit sowie einen nachvollziehbaren Prüfungsaufbau,
    - korrekte Verortung und Durchführung der Inzidentprüfung(en), insbesondere zur Wirksamkeit/Rechtmäßigkeit der Taubenfütterungs-Verordnung,
    - stringente, überzeugende Argumentation, insbesondere an den klausurtypischen Schwerpunktstellen,
    - richtige Zitierung der einschlägigen Normen und Beachtung des Gutachtenstils (Definition – Subsumtion – Ergebnis),
    - grobe sprachliche Mängel können negativ berücksichtigt werden.

Hinweis zur Struktur: Die Reihenfolge einzelner Prüfungspunkte in der Zulässigkeit ist für die Bewertung grundsätzlich unerheblich (ausgenommen: Verwaltungsrechtsweg und statthafte Klageart). Unterschiedliche, vertretbare Orte der Inzidentprüfung sind zu akzeptieren, sofern die Lösung insgesamt stringent und juristisch überzeugend bleibt.

Grundrechtsprüfung: Die Prüfung von Art. 2 Abs. 1 GG und/oder Art. 20a GG sollte grundsätzlich sowohl im Zusammenhang mit Art. 16 LStVG als auch mit der Verordnung möglich sein. Es genügt jedoch, die Grundrechtsprüfung an einer Stelle ausführlich und methodisch tragfähig vorzunehmen.

Beachte außerdem den Bearbeitervermerk im Sachverhalt: Auf das Bayerische Denkmalschutzgesetz, das Infektionsschutzgesetz, das Tiergesundheitsgesetz sowie auf das Tierschutzgesetz ist nicht einzugehen. Vertiefungen zu diesen Normkomplexen sind bei der Bewertung regelmäßig nicht zu honorieren.

Die für die Bewertung relevanten Texte befinden sich in:
    - dem Fall in <sachverhalt>,
    - dem Bewertungsbogen in <bewertungsbogen>,
    - der Antwort in <Studierendenantwort>.

Verwende den Bewertungsbogen in <bewertungsbogen> verbindlich als Grundlage für die Punktevergabe (BE) und die anschließende Notenumrechnung.

Wichtige Hinweise:
    - Berechne am Ende eine Gesamtpunktzahl (0–100 BE) nach dem Bewertungsbogen in <bewertungsbogen>.
    - Sobald die Gesamtpunktzahl der BE ermittelt wurde, ist diese gemäß der Umrechnungstabelle (BE → Note) im Bewertungsbogen in <bewertungsbogen> in eine Note umzuwandeln.
    - Nachdem du diese beiden Schritte durchgeführt hast, gib die Note ausschließlich im folgenden Format aus, ohne Fettdruck, ohne Kursivschrift, ohne zusätzliche Satzzeichen oder Leerzeichen. Dabei steht „X“ für die von dir ermittelte Note:
    
    Note: X

<sachverhalt>
    Taubenfütterungsverbot

    Eine immer größer werdende Taubenpopulation hat in der kreisfreien Stadt S (Oberbayern) in den letzten Jahren zu großen baulichen Schäden an den historischen Gebäuden im Innenstadtbereich geführt. Um dies zu bekämpfen, wurden in der Vergangenheit bereits zwei städtische Taubenhäuser[1] errichtet, die jedoch bis jetzt keine Besserung herbeigeführt haben. Bei einem Kotanfall von 12 kg pro Taube und Jahr und einer geschätzten Population von 50.000 verwilderten Tauben würde, so ein von der Stadt S in Auftrag gegebenes Gutachten, durch ein absolutes Fütterungsverbot Schäden an Gebäuden sowie einer Verbreitung von Krankheitserregern und Parasiten durch die Tauben wirksam begegnet werden können.

    In seiner Sitzung vom 27. März 2025 beschloss der Stadtrat von S mit zwölf zu zehn Stimmen bei drei Enthaltungen den Erlass einer Verordnung über das Verbot des Fütterns verwilderter Tauben (siehe Anlage). Allerdings war die Beschlussfassung über die Verordnung nicht auf der mit der Ladung verschickten Tagesordnung aufgeführt. Vielmehr brachte der Oberbürgermeister den Beratungsgegenstand „Taubenfütterungsverbot“ kurzfristig in die Sitzung ein. Die vollzählig anwesenden Stadtratsmitglieder waren zu Beginn der Sitzung zwar erstaunt über den zusätzlichen Beratungsgegenstand, sodann aber bereit, über diese Angelegenheit zu beraten und abzustimmen. Am 3. April 2025 wurde die Verbotsverordnung im Amtsblatt der Stadt S bekannt gemacht, nachdem der Oberbürgermeister sie zuvor ausgefertigt hatte. 

    Der Rentner Habicht ist entsetzt, dass der Gesetzgeber einen solchen aus seiner Sicht verfassungswidrigen Akt der Tierquälerei – Tierschutz sei verfassungsrechtlich geboten – zulasse und der Gemeinde die Möglichkeit gebe, ihm eine seiner letzten Freuden zu nehmen, da er seit Jahren täglich im Stadtpark von S Tauben füttere. Er beschließt, dieses Verbot zu ignorieren. Mitarbeiter des städtischen Umweltamtes beobachten Habicht, wie er – „aus Protest“ – ab Mitte Mai nunmehr mehrmals täglich nicht nur im Stadtpark, sondern auch unmittelbar vor dem Gebäude des Umweltamtes Tauben füttert. Eine Mitarbeiterin des Umweltamtes weist Habicht am 17. Mai 2025 nochmals auf das Verbot hin. Habicht erklärt, er werde auch weiterhin seine geliebten Tierfreunde vor dem Hungertod bewahren. 

    Hierauf untersagt das für die Vollziehung der Taubenfütterungsverordnung zuständige Umweltamt der Stadt S dem Habicht noch am gleichen Tag schriftlich, weiterhin im Stadtgebiet Tauben zu füttern. Der Bescheid war ordnungsgemäß begründet und enthielt auch eine ordnungsgemäße Rechtsbehelfsbelehrung. 

    Habicht erhebt fristgerecht Klage beim örtlich zuständigen Verwaltungsgericht München und beantragt die Aufhebung des durch den Bescheid angeordneten Fütterungsverbotes. Er sieht unter anderem wesentliche rechtsstaatliche Grundsätze beim Verordnungserlass verletzt: Weder sei ihm aufgrund der lückenhaften Tagesordnung bewusst gewesen, dass der Stadtrat über ein Fütterungsverbot verhandle, noch sei aus der Verordnung ihre Rechtsgrundlage ersichtlich.

    Bearbeitervermerk: Die Erfolgsaussichten der Klage sind zu prüfen. Auf das Bayerische Denkmalschutzgesetz, das Infektionsschutzgesetz, das Tiergesundheitsgesetz sowie auf das Tierschutzgesetz ist nicht einzugehen.

    Anlage: 

    Verordnung der Stadt S über das Verbot des Fütterns verwilderter Tauben 

    § 1
    [Satz 1] Es ist verboten, im Stadtgebiet der Stadt S verwilderte Tauben zu füttern. [Satz 2] Dieses Verbot erfasst auch das Auslegen von Futter- und Lebensmitteln, die erfahrungsgemäß von Tauben aufgenommen werden. [Satz 3] In Vollzug des Verbotes nach Satz 1 und 2 können Anordnungen für den Einzelfall erlassen werden.

    § 2
    Diese Verordnung tritt am 1. Mai 2025 in Kraft.

    Fußnote: [1] Taubenhäuser sind Anlagen, in denen verwilderte Tauben gefüttert werden. Durch diese gezielte Fütterung an einem Ort soll verhindert werden, dass die Tauben ihren Kot in der ganzen Stadt verteilt hinterlassen.
</sachverhalt>


<bewertungsbogen>

    A. ZULÄSSIGKEIT (Gesamt: 19 BE)

    I. Eröffnung des Verwaltungsrechtswegs, § 40 I 1 VwGO – 4 BE
    II. Statthafte Klageart: (P) Verwaltungsakt? – 6 BE
    III. Klagebefugnis, § 42 II VwGO – 2 BE
    IV. Vorverfahren – 1 BE

    V. Beteiligtenbezogene Voraussetzungen
    1. Kläger – 1 BE
    2. Beklagte – 1 BE

    VI. Zuständigkeit des Gerichts
    1. Sachliche Zuständigkeit – 1 BE
    2. Örtliche Zuständigkeit – 1 BE

    VII. Form und Frist
    1. Form – 1 BE
    2. Frist – 1 BE


    B. BEGRÜNDETHEIT (Gesamt: 81 BE)

    Obersatz – 3 BE

    I. Passivlegitimation – 4 BE

    II. Rechtmäßigkeit des Verbotsbescheids

    1. Rechtsgrundlage des Verbotsbescheids – 2 BE

    a) Rechtsgrundlage der Taubenfütterungsverordnung – 3 BE

    aa) Formelle Verfassungsmäßigkeit des Art. 16 LStVG – 1 BE

    bb) Materielle Verfassungsmäßigkeit des Art. 16 LStVG
        (1) Bestimmtheit – 4 BE
        (2) Art. 2 I GG – 7 BE
        (3) Art. 20a GG – 5 BE

    b) Formelle Rechtmäßigkeit der Taubenfütterungsverordnung

    aa) Zuständigkeit der Gemeinde für den Erlass der Verordnung 
        (1) Verbandszuständigkeit – 1 BE
        (2) Organzuständigkeit – 2 BE

    bb) Verfahren
        (1) Beschlussfähigkeit – 6 BE
        (2) Enthaltungen – 3 BE
        (3) Mehrheit – 3 BE
        (4) Öffentlichkeit – 6 BE

    cc) Form
        (1) Zitiergebot – 5 BE
        (2) Ausfertigung und Bekanntmachung – 2 BE

    c) Materielle Rechtmäßigkeit der Verordnung
    aa) Übereinstimmung mit der Rechtsgrundlage – 4 BE
    bb) Kein Verstoß gegen höherrangiges Recht durch die Verordnung 
        (1) Art. 2 I GG – 3 BE (bzw. 7, s. Hinweise)
        (2) Vereinbarkeit mit Art. 20a GG  – 1 BE (bzw. 5, s. Hinweise)
        (3) Bestimmtheitsgebot – 2 BE

    2. Formelle Rechtmäßigkeit des Verbotsbescheids
    a) Zuständigkeit – 2 BE
    b) Verfahren – 1 BE
    c) Form – 1 BE

    3. Materielle Rechtmäßigkeit des Verbotsbescheids
    a) Vereinbarkeit mit der Rechtsgrundlage – 3 BE
    b) Maßnahmerichtung – 1 BE
    c) Ermessen, Verhältnismäßigkeit – 5 BE


    C. GESAMTERGEBNIS – 1 BE

    Summe BE: 100 BE

    Umrechnungstabelle (BE → Note):

    0–9 BE → Note 0
    10–19 BE → Note 1
    20–29 BE → Note 2
    30–39 BE → Note 3
    40–43 BE → Note 4
    44–47 BE → Note 5
    48–51 BE → Note 6
    52–55 BE → Note 7
    56–59 BE → Note 8
    60–63 BE → Note 9
    64–67 BE → Note 10
    68–71 BE → Note 11
    72–75 BE → Note 12
    76–79 BE → Note 13
    80–83 BE → Note 14
    84–87 BE → Note 15
    88–91 BE → Note 16
    92–95 BE → Note 17
    96–100 BE → Note 18

</bewertungsbogen>

Studierendenantwort zur Bewertung:

<Studierendenantwort>
    {student_answer_complete}
</Studierendenantwort>"""

    return prompt