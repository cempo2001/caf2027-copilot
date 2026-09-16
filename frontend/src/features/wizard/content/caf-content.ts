// AUTO-GENERISANO iz CAF_Questions_2.docx (partial adoption, dogovoreno 16.9.2026).
// Statički, dvojezičan sadržaj za Guided Wizard — naziv/uvod/usmjeravajuća pitanja
// po podkriterijumu. NIJE zamjena za backend `subcriteria.name_me/name_en`
// (ta kolona je i dalje izvor istine kad je backend popuni — vidi napomenu u
// alembic/versions/0001_initial_schema.py) — ovo je frontend fallback + dodatni
// sadržaj (uvod, usmjeravajuća pitanja) koji kontrakt trenutno ne prenosi.
//
// NAPOMENA O IZVORU: sadržaj potiče iz eksterno dostavljenog dokumenta koji
// parafrazira CAF 2020 model (nije doslovan citat zvaničnog EIPA teksta) —
// vidi razgovor od 15-16.9.2026. Prije finalnog CER podnošenja preporučuje se
// provjera prema zvaničnom EIPA CAF 2020/2026 dokumentu.

export interface CafSubcriteriaContent {
  code: string;
  criterionNumber: number;
  nameMe: string;
  nameEn: string;
  introductionMe: string;
  introductionEn: string;
  guidingQuestionsMe: string[];
  guidingQuestionsEn: string[];
}

export interface CafCriterionContent {
  number: number;
  nameMe: string;
  nameEn: string;
}

export const CAF_CRITERIA: Record<number, CafCriterionContent> = {
  1: { number: 1, nameMe: "Liderstvo", nameEn: "Leadership" },
  2: { number: 2, nameMe: "Strategija i planiranje", nameEn: "Strategy and Planning" },
  3: { number: 3, nameMe: "Zaposleni", nameEn: "People" },
  4: { number: 4, nameMe: "Partnerstva i resursi", nameEn: "Partnerships and Resources" },
  5: { number: 5, nameMe: "Procesi", nameEn: "Processes" },
  6: { number: 6, nameMe: "Rezultati usmjereni na građane/korisnike", nameEn: "Citizen/Customer-Oriented Results" },
  7: { number: 7, nameMe: "Rezultati u vezi sa zaposlenima", nameEn: "People Results" },
  8: { number: 8, nameMe: "Rezultati društvene odgovornosti", nameEn: "Social Responsibility Results" },
  9: { number: 9, nameMe: "Rezultati ključnog učinka", nameEn: "Key Performance Results" },
};

export const CAF_SUBCRITERIA_CONTENT: Record<string, CafSubcriteriaContent> = {
  "1.1": {
    code: "1.1",
    criterionNumber: 1,
    nameMe: "Rukovodstvo razvija misiju, viziju, vrijednosti i strategiju",
    nameEn: "Leaders develop the mission, vision, values and strategy",
    introductionMe: "Ovaj podkriterijum procjenjuje koliko dobro rukovodstvo razvija i saopštava misiju, viziju, vrijednosti i strategiju institucije. Razmislite da li su jasno definisane, razumljive zaposlenima i da li se aktivno koriste za usmjeravanje odluka.",
    introductionEn: "This subcriterion assesses how well your leaders develop and communicate the organisation's mission, vision, values, and strategy. Think about whether these are clearly defined, understood by staff, and actively used to guide decisions.",
    guidingQuestionsMe: ["Da li vaša institucija ima jasno pisanu izjavu o misiji?", "Da li se izjava o viziji redovno preispituje i ažurira?", "Koliko dobro su organizacione vrijednosti saopštene zaposlenima?", "Da li je strategija usklađena sa misijom i vizijom?", "Koliko često se preispituje sprovođenje strategije?", "Da li rukovodstvo svojim svakodnevnim postupanjem pokazuje vrijednosti institucije?"],
    guidingQuestionsEn: ["Does your organisation have a clearly written mission statement?", "Is the vision statement regularly reviewed and updated?", "How well are organisational values communicated to staff?", "Is the strategy aligned with the mission and vision?", "How often is strategy implementation reviewed?", "Do leaders demonstrate the values in their daily actions?"],
  },
  "1.2": {
    code: "1.2",
    criterionNumber: 1,
    nameMe: "Rukovodstvo podržava sistem upravljanja institucijom",
    nameEn: "Leaders support the organisation's management system",
    introductionMe: "Ovaj podkriterijum sagledava koliko rukovodstvo aktivno podržava i učestvuje u sistemu upravljanja. Razmotrite da li rukovodstvo alocira resurse, učestvuje u pregledima i obezbjeđuje da sistem doprinosi unapređenju.",
    introductionEn: "This subcriterion looks at how leaders actively support and engage with the management system. Consider whether leaders allocate resources, participate in reviews, and ensure the system drives improvement.",
    guidingQuestionsMe: ["Da li rukovodstvo obezbjeđuje dovoljno resursa za sistem upravljanja?", "Koliko često rukovodstvo učestvuje u pregledima upravljanja?", "Da li se sistem upravljanja koristi za pokretanje unapređenja?"],
    guidingQuestionsEn: ["Do leaders allocate adequate resources for the management system?", "How often do leaders participate in management reviews?", "Is the management system used to drive improvement?"],
  },
  "1.3": {
    code: "1.3",
    criterionNumber: 1,
    nameMe: "Rukovodstvo komunicira sa zaposlenima i motiviše ih",
    nameEn: "Leaders communicate with and motivate staff",
    introductionMe: "Ovaj podkriterijum ocjenjuje kako rukovodstvo komunicira sa zaposlenima, motiviše ih i prepoznaje njihov doprinos. Razmislite da li je komunikacija redovna, dvosmjerna i da li se doprinos zaposlenih priznaje.",
    introductionEn: "This subcriterion evaluates how leaders engage with staff through communication, motivation, and recognition. Reflect on whether communication is regular, two-way, and whether staff contributions are acknowledged.",
    guidingQuestionsMe: ["Koliko često rukovodstvo komunicira sa zaposlenima?", "Da li je komunikacija dvosmjerna (rukovodstvo sluša zaposlene)?", "Koliko dobro se prepoznaje doprinos zaposlenih?"],
    guidingQuestionsEn: ["How frequently do leaders communicate with staff?", "Is communication two-way (leaders listen to staff)?", "How well are staff contributions recognised?"],
  },
  "1.4": {
    code: "1.4",
    criterionNumber: 1,
    nameMe: "Rukovodstvo upravlja odnosima sa političkim vlastima i zainteresovanim stranama",
    nameEn: "Leaders manage relationships with political authorities and stakeholders",
    introductionMe: "Ovaj podkriterijum procjenjuje kako rukovodstvo upravlja odnosima sa političkim vlastima i eksternim zainteresovanim stranama. Razmotrite da li se odnosi upravljaju proaktivno, transparentno i da li se potrebe zainteresovanih strana uzimaju u obzir prilikom odlučivanja.",
    introductionEn: "This subcriterion assesses how leaders engage with political authorities and external stakeholders. Consider whether relationships are managed proactively, transparently, and whether stakeholder needs are considered in decision-making.",
    guidingQuestionsMe: ["Da li se odnosi sa političkim vlastima upravljaju proaktivno?", "Koliko dobro se prepoznaju i uzimaju u obzir potrebe zainteresovanih strana?", "Da li se angažovanje zainteresovanih strana preispituje i unapređuje?"],
    guidingQuestionsEn: ["Are relationships with political authorities managed proactively?", "How well are stakeholder needs identified and considered?", "Is stakeholder engagement reviewed and improved?"],
  },
  "2.1": {
    code: "2.1",
    criterionNumber: 2,
    nameMe: "Prepoznavanje potreba i očekivanja zainteresovanih strana, eksternog okruženja i relevantnih upravljačkih informacija",
    nameEn: "Identify the needs and expectations of stakeholders, the external environment, and the relevant management information",
    introductionMe: "Ovaj podkriterijum procjenjuje koliko dobro vaša institucija prepoznaje i razumije potrebe zainteresovanih strana, prati eksterno okruženje i koristi upravljačke informacije za planiranje. Razmotrite da li postoje sistematski procesi za prikupljanje i analizu ovih informacija.",
    introductionEn: "This subcriterion assesses how well your organisation identifies and understands stakeholder needs, monitors the external environment, and uses management information for planning. Consider whether you have systematic processes to gather and analyze this information.",
    guidingQuestionsMe: ["Da li imate sistematski proces za prepoznavanje potreba i očekivanja zainteresovanih strana?", "Koliko dobro pratite i analizirate eksterno okruženje?", "Da li se upravljačke informacije efikasno koriste za strateško planiranje?", "Koliko često se preispituje i ažurira analiza zainteresovanih strana?"],
    guidingQuestionsEn: ["Do you have a systematic process to identify stakeholder needs and expectations?", "How well do you monitor and analyze the external environment?", "Is management information used effectively for strategic planning?", "How often is stakeholder analysis reviewed and updated?"],
  },
  "2.2": {
    code: "2.2",
    criterionNumber: 2,
    nameMe: "Razvoj strategija i planova na osnovu prikupljenih informacija",
    nameEn: "Develop strategies and plans based on gathered information",
    introductionMe: "Ovaj podkriterijum ocjenjuje kako vaša institucija koristi prikupljene informacije za razvoj strategija i planova. Razmotrite da li su strategije zasnovane na dokazima, dobro dokumentovane i usklađene sa potrebama zainteresovanih strana.",
    introductionEn: "This subcriterion evaluates how your organisation uses gathered information to develop strategies and plans. Consider whether strategies are evidence-based, well-documented, and aligned with stakeholder needs.",
    guidingQuestionsMe: ["Da li se strategije razvijaju na osnovu analize zainteresovanih strana i okruženja?", "Koliko dobro su strategije i planovi dokumentovani?", "Da li su strateški ciljevi jasno definisani i mjerljivi?", "Koliko dobro su strategije usklađene sa raspoloživim resursima?"],
    guidingQuestionsEn: ["Are strategies developed based on stakeholder and environmental analysis?", "How well are strategies and plans documented?", "Are strategic objectives clearly defined and measurable?", "How well are strategies aligned with available resources?"],
  },
  "2.3": {
    code: "2.3",
    criterionNumber: 2,
    nameMe: "Saopštavanje, sprovođenje i preispitivanje strategija i planova",
    nameEn: "Communicate, implement, and review strategies and plans",
    introductionMe: "Ovaj podkriterijum sagledava kako se strategije i planovi saopštavaju, sprovode i preispituju. Razmotrite da li zaposleni razumiju strategiju, da li se sprovođenje prati i da li preispitivanja dovode do unapređenja.",
    introductionEn: "This subcriterion looks at how strategies and plans are communicated, implemented, and reviewed. Consider whether staff understand the strategy, implementation is monitored, and reviews lead to improvements.",
    guidingQuestionsMe: ["Koliko dobro su strategije i planovi saopšteni zaposlenima?", "Da li se sprovođenje strategije redovno prati?", "Koliko dobro se strateški planovi sprovode?", "Da li preispitivanja strategije dovode do unapređenja?"],
    guidingQuestionsEn: ["How well are strategies and plans communicated to staff?", "Is strategy implementation monitored regularly?", "How well are strategic plans implemented?", "Do strategy reviews lead to improvements?"],
  },
  "2.4": {
    code: "2.4",
    criterionNumber: 2,
    nameMe: "Upravljanje promjenama i inovacijama radi agilnosti i otpornosti institucije",
    nameEn: "Manage change and innovation to ensure the agility and resilience of the organisation",
    introductionMe: "Ovaj podkriterijum procjenjuje kako vaša institucija upravlja promjenama i inovacijama. Razmotrite da li postoje procesi za upravljanje promjenama, da li se podstiču inovacije i da li se gradi organizaciona otpornost.",
    introductionEn: "This subcriterion assesses how your organisation manages change and innovation. Consider whether you have processes for change management, encourage innovation, and build organizational resilience.",
    guidingQuestionsMe: ["Da li imate strukturiran proces upravljanja promjenama?", "Koliko dobro vaša institucija podstiče i podržava inovacije?", "Koliko je vaša institucija agilna u odgovoru na promjene?", "Da li se upravljanje promjenama preispituje i unapređuje?"],
    guidingQuestionsEn: ["Do you have a structured change management process?", "How well does your organisation encourage and support innovation?", "How agile is your organisation in responding to changes?", "Is change management reviewed and improved?"],
  },
  "3.1": {
    code: "3.1",
    criterionNumber: 3,
    nameMe: "Upravljanje i unapređenje ljudskih resursa u podršci strategiji i planiranju institucije",
    nameEn: "Manage and improve human resources to support the strategy and planning of the organisation",
    introductionMe: "Ovaj podkriterijum ocjenjuje kako vaša institucija upravlja ljudskim resursima u podršci strateškim ciljevima. Razmotrite da li je planiranje ljudskih resursa usklađeno sa strategijom, da li se resursi efikasno raspoređuju i da li se procesi upravljanja ljudskim resursima kontinuirano unapređuju.",
    introductionEn: "This subcriterion evaluates how your organisation manages human resources to support strategic objectives. Consider whether HR planning aligns with strategy, resources are allocated effectively, and HR processes are continuously improved.",
    guidingQuestionsMe: ["Da li je planiranje ljudskih resursa usklađeno sa strategijom institucije?", "Koliko dobro su ljudski resursi raspoređeni u podršci strateškim ciljevima?", "Da li se procesi upravljanja ljudskim resursima redovno preispituju i unapređuju?"],
    guidingQuestionsEn: ["Is human resource planning aligned with organisational strategy?", "How well are human resources allocated to support strategic objectives?", "Are HR processes regularly reviewed and improved?"],
  },
  "3.2": {
    code: "3.2",
    criterionNumber: 3,
    nameMe: "Razvoj i upravljanje kompetencijama zaposlenih",
    nameEn: "Develop and manage competencies of people",
    introductionMe: "Ovaj podkriterijum procjenjuje kako vaša institucija razvija i upravlja kompetencijama zaposlenih. Razmotrite da li se prepoznaju potrebe za kompetencijama, da li se pružaju mogućnosti obuke i razvoja i da li se nivo kompetencija ocjenjuje.",
    introductionEn: "This subcriterion assesses how your organisation develops and manages employee competencies. Consider whether you identify competency needs, provide training and development opportunities, and assess competency levels.",
    guidingQuestionsMe: ["Da li imate sistematski proces za prepoznavanje potreba za kompetencijama?", "Koliko dobro se pružaju mogućnosti obuke i razvoja?", "Da li se nivo kompetencija redovno ocjenjuje?"],
    guidingQuestionsEn: ["Do you have a systematic process to identify competency needs?", "How well are training and development opportunities provided?", "Are competency levels regularly assessed?"],
  },
  "3.3": {
    code: "3.3",
    criterionNumber: 3,
    nameMe: "Uključivanje i osnaživanje zaposlenih i podrška njihovoj dobrobiti",
    nameEn: "Involve and empower people and support their well-being",
    introductionMe: "Ovaj podkriterijum sagledava kako vaša institucija uključuje i osnažuje zaposlene i podržava njihovu dobrobit. Razmotrite da li su zaposleni uključeni u odlučivanje, da li imaju autonomiju i da li se dobrobit aktivno podržava.",
    introductionEn: "This subcriterion looks at how your organisation involves and empowers employees, and supports their well-being. Consider whether staff are engaged in decision-making, have autonomy, and whether well-being is actively supported.",
    guidingQuestionsMe: ["Koliko dobro su zaposleni uključeni u odlučivanje?", "Koliko dobro su zaposleni osnaženi da preuzimaju inicijativu?", "Koliko dobro se podržava dobrobit zaposlenih?"],
    guidingQuestionsEn: ["How well are people involved in decision-making?", "How well are people empowered to take initiative?", "How well is employee well-being supported?"],
  },
  "4.1": {
    code: "4.1",
    criterionNumber: 4,
    nameMe: "Razvoj i upravljanje partnerstvima sa relevantnim organizacijama",
    nameEn: "Develop and manage partnerships with relevant organisations",
    introductionMe: "Ovaj podkriterijum procjenjuje kako vaša institucija razvija i upravlja partnerstvima sa drugim organizacijama. Razmotrite da li su partnerstva strateški odabrana, dobro upravljana i da li doprinose ostvarenju ciljeva.",
    introductionEn: "This subcriterion assesses how your organisation develops and manages partnerships with other organisations. Consider whether partnerships are strategically selected, well-managed, and contribute to achieving objectives.",
    guidingQuestionsMe: ["Da li imate strateški pristup odabiru partnera?", "Koliko dobro se partnerstva upravljaju i prate?", "Da li partnerstva efikasno doprinose strateškim ciljevima?"],
    guidingQuestionsEn: ["Do you have a strategic approach to selecting partners?", "How well are partnerships managed and monitored?", "Do partnerships contribute effectively to strategic objectives?"],
  },
  "4.2": {
    code: "4.2",
    criterionNumber: 4,
    nameMe: "Razvoj i sprovođenje partnerstava sa građanima i organizacijama civilnog društva",
    nameEn: "Develop and implement partnerships with citizens and civil society organisations",
    introductionMe: "Ovaj podkriterijum ocjenjuje kako se vaša institucija angažuje sa građanima i civilnim društvom. Razmotrite da li postoje mehanizmi za učešće građana, da li sarađujete sa civilnim društvom i da li su ta partnerstva efikasna.",
    introductionEn: "This subcriterion evaluates how your organisation engages with citizens and civil society. Consider whether you have mechanisms for citizen participation, collaborate with civil society, and whether these partnerships are effective.",
    guidingQuestionsMe: ["Da li imate mehanizme za učešće i uključivanje građana?", "Koliko dobro sarađujete sa organizacijama civilnog društva?", "Da li se partnerstva sa građanima i civilnim društvom preispituju radi ocjene efikasnosti?"],
    guidingQuestionsEn: ["Do you have mechanisms for citizen participation and engagement?", "How well do you collaborate with civil society organisations?", "Are citizen and civil society partnerships reviewed for effectiveness?"],
  },
  "4.3": {
    code: "4.3",
    criterionNumber: 4,
    nameMe: "Upravljanje finansijama",
    nameEn: "Manage finances",
    introductionMe: "Ovaj podkriterijum procjenjuje kako vaša institucija upravlja finansijskim resursima. Razmotrite da li je finansijsko planiranje strateško, da li se budžeti efikasno upravljaju i da li se finansijski učinak prati.",
    introductionEn: "This subcriterion assesses how your organisation manages financial resources. Consider whether financial planning is strategic, budgets are managed effectively, and financial performance is monitored.",
    guidingQuestionsMe: ["Da li je finansijsko planiranje usklađeno sa strateškim ciljevima?", "Koliko dobro se budžeti upravljaju i kontrolišu?", "Da li se finansijski učinak redovno prati i izvještava?"],
    guidingQuestionsEn: ["Is financial planning aligned with strategic objectives?", "How well are budgets managed and controlled?", "Is financial performance regularly monitored and reported?"],
  },
  "4.4": {
    code: "4.4",
    criterionNumber: 4,
    nameMe: "Upravljanje informacijama i znanjem",
    nameEn: "Manage information and knowledge",
    introductionMe: "Ovaj podkriterijum ocjenjuje kako vaša institucija upravlja informacijama i znanjem. Razmotrite da li su informacije dostupne, da li se znanje dijeli i da li informacioni sistemi efikasno podržavaju odlučivanje.",
    introductionEn: "This subcriterion evaluates how your organisation manages information and knowledge. Consider whether information is accessible, knowledge is shared, and whether information systems support decision-making effectively.",
    guidingQuestionsMe: ["Koliko su informacije dostupne zaposlenima kojima su potrebne?", "Koliko dobro se znanje dijeli unutar institucije?", "Da li informacioni sistemi efikasno podržavaju odlučivanje?"],
    guidingQuestionsEn: ["How accessible is information to staff who need it?", "How well is knowledge shared across the organisation?", "Do information systems effectively support decision-making?"],
  },
  "4.5": {
    code: "4.5",
    criterionNumber: 4,
    nameMe: "Upravljanje tehnologijom",
    nameEn: "Manage technology",
    introductionMe: "Ovaj podkriterijum procjenjuje kako vaša institucija upravlja tehnologijom. Razmotrite da li je tehnologija usklađena sa potrebama, da li se dobro održava i da li IT sistemi efikasno podržavaju rad.",
    introductionEn: "This subcriterion assesses how your organisation manages technology. Consider whether technology is aligned with needs, well-maintained, and whether IT systems support operations effectively.",
    guidingQuestionsMe: ["Da li je tehnologija usklađena sa potrebama i strategijom institucije?", "Koliko dobro se IT sistemi održavaju i ažuriraju?", "Da li IT sistemi efikasno podržavaju svakodnevni rad?"],
    guidingQuestionsEn: ["Is technology aligned with organisational needs and strategy?", "How well are IT systems maintained and updated?", "Do IT systems effectively support operations?"],
  },
  "4.6": {
    code: "4.6",
    criterionNumber: 4,
    nameMe: "Upravljanje prostorom i objektima",
    nameEn: "Manage facilities",
    introductionMe: "Ovaj podkriterijum ocjenjuje kako vaša institucija upravlja prostorom i fizičkim resursima. Razmotrite da li su objekti dobro održavani, prilagođeni radu i da li podržavaju dobrobit zaposlenih.",
    introductionEn: "This subcriterion evaluates how your organisation manages facilities and physical resources. Consider whether facilities are well-maintained, suitable for operations, and whether they support staff well-being.",
    guidingQuestionsMe: ["Da li su objekti prilagođeni operativnim potrebama?", "Koliko dobro se objekti održavaju?", "Da li objekti podržavaju dobrobit i produktivnost zaposlenih?"],
    guidingQuestionsEn: ["Are facilities suitable for operational needs?", "How well are facilities maintained?", "Do facilities support staff well-being and productivity?"],
  },
  "5.1": {
    code: "5.1",
    criterionNumber: 5,
    nameMe: "Oblikovanje i upravljanje procesima radi pružanja vrijednosti građanima/korisnicima i ostvarenja strateških ciljeva",
    nameEn: "Design and manage processes to deliver citizen/customer value and achieve strategic objectives",
    introductionMe: "Ovaj podkriterijum procjenjuje kako vaša institucija oblikuje i upravlja procesima. Razmotrite da li su procesi usmjereni na korisnika, dobro dokumentovani i da li doprinose ostvarenju strateških ciljeva.",
    introductionEn: "This subcriterion assesses how your organisation designs and manages processes. Consider whether processes are customer-focused, well-documented, and whether they contribute to achieving strategic objectives.",
    guidingQuestionsMe: ["Da li se procesi oblikuju imajući u vidu vrijednost za građane/korisnike?", "Koliko dobro su ključni procesi dokumentovani?", "Da li procesi efikasno doprinose strateškim ciljevima?", "Da li se procesi redovno preispituju i unapređuju?"],
    guidingQuestionsEn: ["Are processes designed with citizen/customer value in mind?", "How well are key processes documented?", "Do processes contribute effectively to strategic objectives?", "Are processes regularly reviewed and improved?"],
  },
  "5.2": {
    code: "5.2",
    criterionNumber: 5,
    nameMe: "Razvoj i pružanje usluga i proizvoda usmjerenih na građane/korisnike",
    nameEn: "Develop and deliver citizen/customer-oriented services and products",
    introductionMe: "Ovaj podkriterijum ocjenjuje kako vaša institucija razvija i pruža usluge i proizvode. Razmotrite da li usluge odgovaraju potrebama korisnika, da li su dostupne i da li se povratne informacije korisnika koriste za unapređenje.",
    introductionEn: "This subcriterion evaluates how your organisation develops and delivers services and products. Consider whether services meet customer needs, are accessible, and whether customer feedback is used for improvement.",
    guidingQuestionsMe: ["Da li se usluge i proizvodi oblikuju na osnovu potreba građana/korisnika?", "Koliko su usluge dostupne građanima/korisnicima?", "Da li se povratne informacije građana/korisnika koriste za unapređenje usluga?"],
    guidingQuestionsEn: ["Are services and products designed based on citizen/customer needs?", "How accessible are services to citizens/customers?", "Is citizen/customer feedback used to improve services?"],
  },
  "5.3": {
    code: "5.3",
    criterionNumber: 5,
    nameMe: "Inoviranje procesa uz uključivanje građana/korisnika",
    nameEn: "Innovate processes involving citizens/customers",
    introductionMe: "Ovaj podkriterijum sagledava kako vaša institucija inovira procese uz uključivanje građana/korisnika. Razmotrite da li aktivno tražite mogućnosti za inovacije, da li uključujete korisnike u inovacije i da li se inovacije efikasno sprovode.",
    introductionEn: "This subcriterion looks at how your organisation innovates processes with citizen/customer involvement. Consider whether you actively seek innovation opportunities, involve customers in innovation, and whether innovations are implemented effectively.",
    guidingQuestionsMe: ["Da li aktivno tražite mogućnosti za inovacije u procesima?", "Koliko dobro su građani/korisnici uključeni u inovacije procesa?", "Da li se inovacije procesa efikasno sprovode?"],
    guidingQuestionsEn: ["Do you actively seek innovation opportunities in processes?", "How well are citizens/customers involved in process innovation?", "Are process innovations effectively implemented?"],
  },
  "6.1": {
    code: "6.1",
    criterionNumber: 6,
    nameMe: "Mjerenje percepcije",
    nameEn: "Perception measurements",
    introductionMe: "Ovaj podkriterijum procjenjuje rezultate percepcije građana/korisnika. Razmotrite da li mjerite zadovoljstvo, povjerenje i percepciju, i da li ta mjerenja pokazuju pozitivan trend.",
    introductionEn: "This subcriterion assesses citizen/customer perception results. Consider whether you measure satisfaction, trust, and perceptions, and whether these measurements show positive trends.",
    guidingQuestionsMe: ["Da li redovno mjerite zadovoljstvo građana/korisnika?", "Kakav je trend zadovoljstva građana/korisnika?", "Da li imate ciljeve za zadovoljstvo građana/korisnika?", "Kako građani/korisnici percipiraju kvalitet usluga?"],
    guidingQuestionsEn: ["Do you regularly measure citizen/customer satisfaction?", "What is the trend in citizen/customer satisfaction?", "Do you have targets for citizen/customer satisfaction?", "How do citizens/customers perceive service quality?"],
  },
  "6.2": {
    code: "6.2",
    criterionNumber: 6,
    nameMe: "Mjerenje učinka",
    nameEn: "Performance measurements",
    introductionMe: "Ovaj podkriterijum ocjenjuje rezultate učinka u vezi sa uslugama za građane/korisnike. Razmotrite da li mjerite učinak pružanja usluga, dostupnost i rješavanje pritužbi, i da li se učinak poboljšava.",
    introductionEn: "This subcriterion evaluates performance results related to citizen/customer services. Consider whether you measure service delivery performance, accessibility, and complaint resolution, and whether performance is improving.",
    guidingQuestionsMe: ["Da li mjerite učinak pružanja usluga (npr. vrijeme odgovora, stopu završetka)?", "Kakav je trend učinka pružanja usluga?", "Koliko dobro se rješavaju pritužbe građana/korisnika?", "Da li imate ciljeve učinka i da li se oni ostvaruju?"],
    guidingQuestionsEn: ["Do you measure service delivery performance (e.g., response times, completion rates)?", "What is the trend in service delivery performance?", "How well are citizen/customer complaints handled?", "Do you have performance targets and are they being met?"],
  },
  "7.1": {
    code: "7.1",
    criterionNumber: 7,
    nameMe: "Mjerenje percepcije",
    nameEn: "Perception measurements",
    introductionMe: "Ovaj podkriterijum procjenjuje rezultate percepcije zaposlenih. Razmotrite da li mjerite zadovoljstvo, motivaciju i angažovanost zaposlenih, i da li ta mjerenja pokazuju pozitivan trend.",
    introductionEn: "This subcriterion assesses employee perception results. Consider whether you measure employee satisfaction, motivation, and engagement, and whether these measurements show positive trends.",
    guidingQuestionsMe: ["Da li redovno mjerite zadovoljstvo i angažovanost zaposlenih?", "Kakav je trend zadovoljstva zaposlenih?", "Koliko su zaposleni motivisani i angažovani?", "Da li imate ciljeve za zadovoljstvo i angažovanost zaposlenih?"],
    guidingQuestionsEn: ["Do you regularly measure employee satisfaction and engagement?", "What is the trend in employee satisfaction?", "How motivated and engaged are employees?", "Do you have targets for employee satisfaction and engagement?"],
  },
  "7.2": {
    code: "7.2",
    criterionNumber: 7,
    nameMe: "Mjerenje učinka",
    nameEn: "Performance measurements",
    introductionMe: "Ovaj podkriterijum ocjenjuje rezultate učinka u vezi sa zaposlenima. Razmotrite da li mjerite odsustvovanje, fluktuaciju, razvoj kompetencija i produktivnost, i da li se učinak poboljšava.",
    introductionEn: "This subcriterion evaluates performance results related to people. Consider whether you measure absenteeism, turnover, competency development, and productivity, and whether performance is improving.",
    guidingQuestionsMe: ["Da li mjerite ključne pokazatelje učinka u vezi sa zaposlenima (odsustvovanje, fluktuacija, produktivnost)?", "Kakav je trend odsustvovanja i fluktuacije?", "Koliko dobro napreduje razvoj kompetencija?", "Da li imate ciljeve učinka za pokazatelje vezane za zaposlene i da li se oni ostvaruju?"],
    guidingQuestionsEn: ["Do you measure key people performance indicators (absenteeism, turnover, productivity)?", "What is the trend in absenteeism and turnover?", "How well is competency development progressing?", "Do you have performance targets for people indicators and are they being met?"],
  },
  "8.1": {
    code: "8.1",
    criterionNumber: 8,
    nameMe: "Mjerenje percepcije",
    nameEn: "Perception measurements",
    introductionMe: "Ovaj podkriterijum procjenjuje rezultate percepcije u vezi sa društvenom odgovornošću. Razmotrite da li mjerite kako zainteresovane strane percipiraju vaš društveni i ekološki učinak, i da li je ta percepcija pozitivna.",
    introductionEn: "This subcriterion assesses perception results related to social responsibility. Consider whether you measure how stakeholders perceive your social and environmental performance, and whether these perceptions are positive.",
    guidingQuestionsMe: ["Da li mjerite percepciju zainteresovanih strana o društvenoj odgovornosti?", "Kakav je trend percepcije o društvenoj odgovornosti?", "Kako zainteresovane strane percipiraju vaš ekološki učinak?", "Da li imate ciljeve za percepciju društvene odgovornosti?"],
    guidingQuestionsEn: ["Do you measure stakeholder perceptions of social responsibility?", "What is the trend in social responsibility perceptions?", "How do stakeholders perceive your environmental performance?", "Do you have targets for social responsibility perceptions?"],
  },
  "8.2": {
    code: "8.2",
    criterionNumber: 8,
    nameMe: "Mjerenje učinka",
    nameEn: "Performance measurements",
    introductionMe: "Ovaj podkriterijum ocjenjuje rezultate učinka u vezi sa društvenom odgovornošću. Razmotrite da li mjerite uticaj na životnu sredinu, angažovanje zajednice i održivost, i da li se učinak poboljšava.",
    introductionEn: "This subcriterion evaluates performance results related to social responsibility. Consider whether you measure environmental impact, community engagement, and sustainability, and whether performance is improving.",
    guidingQuestionsMe: ["Da li mjerite pokazatelje učinka na životnu sredinu (npr. potrošnju energije, otpad, emisije)?", "Kakav je trend učinka na životnu sredinu?", "Koliko dobro se angažujete sa zajednicom?", "Da li imate ciljeve za ekološki i društveni učinak?"],
    guidingQuestionsEn: ["Do you measure environmental performance indicators (e.g., energy use, waste, emissions)?", "What is the trend in environmental performance?", "How well do you engage with the community?", "Do you have targets for environmental and social performance?"],
  },
  "9.1": {
    code: "9.1",
    criterionNumber: 9,
    nameMe: "Eksterni rezultati",
    nameEn: "External results",
    introductionMe: "Ovaj podkriterijum procjenjuje eksterne rezultate učinka. Razmotrite da li mjerite pružanje usluga, efikasnost i ostvarenje strateških ciljeva, i da li se ovi rezultati poboljšavaju.",
    introductionEn: "This subcriterion assesses external performance results. Consider whether you measure service delivery, efficiency, and achievement of strategic objectives, and whether these results are improving.",
    guidingQuestionsMe: ["Da li mjerite ključne eksterne pokazatelje učinka?", "Kakav je trend eksternih rezultata učinka?", "Koliko dobro se ostvaruju strateški ciljevi?", "Da li imate ciljeve za eksterni učinak i da li se oni ostvaruju?"],
    guidingQuestionsEn: ["Do you measure key external performance indicators?", "What is the trend in external performance results?", "How well are strategic objectives being achieved?", "Do you have targets for external performance and are they being met?"],
  },
  "9.2": {
    code: "9.2",
    criterionNumber: 9,
    nameMe: "Interni rezultati",
    nameEn: "Internal results",
    introductionMe: "Ovaj podkriterijum ocjenjuje interne rezultate učinka. Razmotrite da li mjerite operativnu efikasnost, kvalitet i iskorišćenost resursa, i da li se ovi rezultati poboljšavaju.",
    introductionEn: "This subcriterion evaluates internal performance results. Consider whether you measure operational efficiency, quality, and resource utilization, and whether these results are improving.",
    guidingQuestionsMe: ["Da li mjerite ključne interne pokazatelje učinka (efikasnost, kvalitet, iskorišćenost resursa)?", "Kakav je trend operativne efikasnosti?", "Koliko dobro se upravlja kvalitetom i unapređuje?", "Da li imate ciljeve za interni učinak i da li se oni ostvaruju?"],
    guidingQuestionsEn: ["Do you measure key internal performance indicators (efficiency, quality, resource use)?", "What is the trend in operational efficiency?", "How well is quality managed and improved?", "Do you have targets for internal performance and are they being met?"],
  },
};

export function getCafSubcriteriaContent(code: string): CafSubcriteriaContent | undefined {
  return CAF_SUBCRITERIA_CONTENT[code];
}

