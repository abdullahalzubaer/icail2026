def create_prompt_v1_ta_min_dp(student_answer_complete):

    prompt = f"""Du bist ein erfahrener Prüfer für juristische Universitätsklausuren und bewertest die Studierendenantwort nach allgemeinen akademischen Bewertungsmaßstäben unter Berücksichtigung von Kohärenz, Vollständigkeit und der Qualität der Begründung.

Nutze dabei für die Bewertung ausschließlich:
    - den Fall in <sachverhalt>,
    - die Antwort in <Studierendenantwort>,
    und stütze dich bei der Bewertung auf dein eigenes juristisches Fachwissen.

Wichtige Hinweise:
    - Vergib am Ende eine ganzzahlige Note X im Bereich von 0 bis 18.
    - 0 bedeutet, dass die Studierendenantwort praktisch unbrauchbar ist (z.B. keine einschlägigen rechtlichen Ausführungen, völlig am Sachverhalt vorbei).
    - 18 bedeutet, dass die Studierendenantwort besonders hervorragend und nahezu perfekt ist (vollständige Erfassung der relevanten Probleme, zutreffende Anwendung der maßgeblichen rechtlichen Maßstäbe und überzeugende Begründung).
    - Dazwischen sollen die Noten abgestuft nach dem Gesamteindruck der Leistung vergeben werden: Je besser die Studierendenantwort inhaltlich, strukturell und argumentativ den nach deiner juristischen Fachkenntnis zutreffenden Anforderungen an eine sehr gute Lösung entspricht, desto höher die Note.
    - Nachdem du diese Bewertung vorgenommen hast, gib die Note ausschließlich im folgenden Format aus, ohne Fettdruck, ohne Kursivschrift, ohne zusätzliche Satzzeichen oder Leerzeichen. Dabei steht „X“ für die von dir ermittelte Note:

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

Studierendenantwort zur Bewertung:

<Studierendenantwort>
    {student_answer_complete}
</Studierendenantwort>"""

    return prompt