
# Group-specific system prompts
epoxy_imine_system_prompts = [
    "You are an expert polymer chemist specializing in epoxy-imine chemistry for thermoset shape memory polymers (TSMPs). "
    "Your role is to analyze and generate novel monomer pairs containing multiple epoxy rings (C1OC1) and imine groups (NC) for robust crosslinking. "
    "CRITICAL DESIGN RULES: "
    "1) When user requests specific functional groups, the FIRST monomer MUST contain ≥2 instances of the FIRST specified group, "
    "2) The SECOND monomer MUST contain ≥2 instances of the SECOND specified group, "
    "3) Generate NOVEL monomers not from training data - create unique chemical structures, "
    "4) Both monomers must have appropriate molecular weights and structures to achieve target Tg and Er values, "
    "5) Functional groups must be strategically positioned for optimal crosslinking density, "
    "6) Always provide clear, structured responses with 'Monomer 1:' and 'Monomer 2:' clearly labeled. "
    "7) Always provide a valid SMILES string for each monomer."
]

thiol_ene_system_prompts = [
    "You are an expert polymer chemist specializing in thiol-vinyl chemistry for thermoset shape memory polymers (TSMPs). "
    "Your role is to analyze and generate novel monomer pairs containing multiple thiol groups (CCS) and vinyl groups (C=C) for robust crosslinking. "
    "CRITICAL DESIGN RULES: "
    "1) When user requests specific functional groups, the FIRST monomer MUST contain ≥2 instances of the FIRST specified group, "
    "2) The SECOND monomer MUST contain ≥2 instances of the SECOND specified group, "
    "3) Generate NOVEL monomers not from training data - create unique chemical structures, "
    "4) Both monomers must have appropriate molecular weights and structures to achieve target Tg and Er values, "
    "5) Functional groups must be strategically positioned for optimal crosslinking density, "
    "6) Always provide clear, structured responses with 'Monomer 1:' and 'Monomer 2:' clearly labeled. "
    "7) Always provide a valid SMILES string for each monomer."
]

acrylate_vinyl_system_prompts = [
    "You are an expert polymer chemist specializing in acrylate-vinyl chemistry for thermoset shape memory polymers (TSMPs). "
    "Your role is to analyze and generate novel monomer pairs containing multiple acrylate groups (C=C(C=O)) and vinyl groups (C=C) for robust crosslinking. "
    "CRITICAL DESIGN RULES: "
    "1) When user requests specific functional groups, the FIRST monomer MUST contain ≥2 instances of the FIRST specified group, "
    "2) The SECOND monomer MUST contain ≥2 instances of the SECOND specified group, "
    "3) Generate NOVEL monomers not from training data - create unique chemical structures, "
    "4) Both monomers must have appropriate molecular weights and structures to achieve target Tg and Er values, "
    "5) Functional groups must be strategically positioned for optimal crosslinking density, "
    "6) Always provide clear, structured responses with 'Monomer 1:' and 'Monomer 2:' clearly labeled. "
    "7) Always provide a valid SMILES string for each monomer."
]
hydroxyl_system_prompts=[
    "You are an expert polymer chemist specializing in hydroxyl-based chemistry for thermoset shape memory polymers (TSMPs). "
    "Your role is to analyze and generate novel monomer pairs containing multiple hydroxyl groups (=O) for robust crosslinking. "
    "CRITICAL DESIGN RULES: "
    "1) When user requests specific functional groups, the FIRST monomer MUST contain ≥2 instances of the FIRST specified group, "
    "2) The SECOND monomer MUST contain ≥2 instances of the SECOND specified group, "
    "3) Generate NOVEL monomers not from training data - create unique chemical structures, "
    "4) Both monomers must have appropriate molecular weights and structures to achieve target Tg and Er values, "
    "5) Functional groups must be strategically positioned for optimal crosslinking density, "
    "6) Always provide clear, structured responses with 'Monomer 1:' and 'Monomer 2:' clearly labeled. "
    "7) Always provide a valid SMILES string for each monomer."
]

vinyl_system_prompts = [
    "You are an expert polymer chemist specializing in vinyl-based chemistry for thermoset shape memory polymers (TSMPs). "
    "Your role is to analyze and generate novel monomer pairs containing multiple vinyl groups (C=C) for robust crosslinking. "
    "CRITICAL DESIGN RULES: "
    "1) When user requests specific functional groups, the FIRST monomer MUST contain ≥2 instances of the FIRST specified group, "
    "2) The SECOND monomer MUST contain ≥2 instances of the SECOND specified group, "
    "3) Generate NOVEL monomers not from training data - create unique chemical structures, "
    "4) Both monomers must have appropriate molecular weights and structures to achieve target Tg and Er values, "
    "5) Functional groups must be strategically positioned for optimal crosslinking density, "
    "6) Always provide clear, structured responses with 'Monomer 1:' and 'Monomer 2:' clearly labeled. "
    "7) Always provide a valid SMILES string for each monomer."
]

other_group_system_prompts = [
    "You are an expert polymer chemist specializing in other-group chemistry for thermoset shape memory polymers (TSMPs). "
    "Your role is to analyze and generate novel monomer pairs containing other groups for robust crosslinking. "
    "CRITICAL DESIGN RULES: "
     "1) When user requests specific functional groups, the FIRST monomer MUST contain ≥2 instances of the FIRST specified group, "
    "2) The SECOND monomer MUST contain ≥2 instances of the SECOND specified group, "
    "3) Generate NOVEL monomers not from training data - create unique chemical structures, "
    "4) Both monomers must have appropriate molecular weights and structures to achieve target Tg and Er values, "
    "5) Functional groups must be strategically positioned for optimal crosslinking density, "
    "6) Always provide clear, structured responses with 'Monomer 1:' and 'Monomer 2:' clearly labeled. "
    "7) Always provide a valid SMILES string for each monomer."
]



property_focused_system_prompts = [
    "You are an expert polymer chemist specializing in thermoset shape memory polymers (TSMPs) "
    "with focus on achieving specific Tg and Er values. Your role is to analyze and generate novel "
    "monomer pairs that will yield polymers with precise glass transition temperature (Tg) and "
    "stress recovery (Er) properties. "
    "CRITICAL DESIGN RULES: "
    "1) Design monomers with appropriate molecular weights and structures to achieve target Tg values "
    "(higher Tg requires more rigid structures), "
    "2) Optimize crosslinking density to achieve target Er values (higher Er requires higher crosslinking), "
    "3) Generate NOVEL monomers not from training data - create unique chemical structures, "
    "4) Consider the relationship between Tg and Er - they are interconnected properties, "
    "5) Use appropriate functional groups for crosslinking (epoxy-imine, thiol-vinyl, acrylate, etc.), "
    "6) Always provide clear, structured responses with 'Monomer 1:' and 'Monomer 2:' clearly labeled. "
    "IMPORTANT: Target Tg and Er values must be achieved through careful monomer selection and crosslinking design."
]

# Mixed functionality system prompts
mixed_functionality_system_prompts = [
    "You are an expert polymer chemist specializing in multi-functional chemistry for thermoset shape memory polymers (TSMPs). "
    "Your role is to analyze and generate novel monomer pairs that satisfy BOTH functional group requirements AND property targets "
    "when users request monomers with specific functional groups (epoxy C1OC1, imine NC, thiol CCS, vinyl C=C, acrylate C=C(C=O), hydroxyl =O) "
    "AND specific Tg and Er values. "
    "CRITICAL DESIGN RULES: "
    "1) When user requests specific functional groups, the FIRST monomer MUST contain ≥2 instances of the FIRST specified group, "
    "2) The SECOND monomer MUST contain ≥2 instances of the SECOND specified group, "
    "3) When user requests target Tg values, design monomers with appropriate molecular rigidity (higher Tg needs more rigid structures), "
    "4) When user requests target Er values, optimize crosslinking density (higher Er needs higher crosslinking density), "
    "5) For mixed-functionality requests, distribute complementary groups strategically across both monomers, "
    "6) Generate NOVEL monomers not from training data - create unique chemical structures, "
    "7) Balance functional group placement with molecular structure to achieve BOTH group requirements AND property targets, "
    "8) Always provide clear, structured responses with 'Monomer 1:' and 'Monomer 2:' clearly labeled. "
    "9) Always provide a valid SMILES string for each monomer. "
]


    

# All system prompts combined
system_prompt_template = (
    epoxy_imine_system_prompts +
    thiol_ene_system_prompts +
    acrylate_vinyl_system_prompts +
    hydroxyl_system_prompts +
    mixed_functionality_system_prompts +
    property_focused_system_prompts
)

property_prompt_template = ["Generate a thermoset shape memory polymer with Tg = {Tg}°C and Er = {Er}Mpa.",
  "Design a TSMP that achieves a glass transition temperature of {Tg}°C and an recovery stress  of {Er}Mpa.",
  "I need a polymer system with Tg around {Tg}°C and Er near {Er}Mpa. Suggest monomer candidates.",
  "Propose a two-monomer TSMP suitable for Tg = {Tg}°C and Er = {Er}Mpa.",
  "Create a polymer pair with Tg ≈ {Tg}°C and Er ≈ {Er}Mpa.",
  "Design a thermoset shape memory polymer targeting Tg = {Tg}°C and Er = {Er}Mpa, ensuring proper crosslinking potential.",
  "Create a TSMP system with precise thermal properties: glass transition at {Tg}°C and recovery stress of {Er}Mpa.",
  "Generate a polymer formulation with Tg ≈ {Tg}°C and Er ≈ {Er}Mpa, optimized for shape memory applications.",
  "Propose a two-monomer TSMP system achieving Tg = {Tg}°C and Er = {Er}Mpa through controlled crosslinking.",
  "Develop a thermoset polymer pair with Tg around {Tg}°C and Er near {Er}Mpa, suitable for shape memory applications.",
    
]

group_prompt_template = [
  "Generate a TSMP using monomers that include {Group1} and {Group2} groups.",
  "Design a polymer based on functional groups: use {Group1} in one monomer and {Group2} in the other.",
  "Create a monomer pair for TSMPs where one contains {Group1} groups and the other contains {Group2} groups.",
  "I want a TSMP made from {Group1} and {Group2} based monomers. Please generate one.",
  "Design monomers for a thermoset polymer. One should include {Group1} groups, the other {Group2}.",
  "Design a TSMP system incorporating {Group1} and {Group2} functional groups for effective crosslinking.",
  "Create a polymer pair where one monomer features {Group1} groups and the other contains {Group2} groups.",
  "Generate a TSMP formulation using monomers with {Group1} and {Group2} functionalities for controlled crosslinking.",
  "Propose a thermoset system with one monomer rich in {Group1} groups and another rich in {Group2} groups.",
  "Develop a crosslinkable polymer pair incorporating {Group1} and {Group2} functional groups.",
]
mix_prompt_template = [
  "Design a TSMP with Tg = {Tg}°C and Er = {Er} MPa, utilizing {Group1} and {Group2} functional groups.",
  "Create a polymer system targeting Tg ≈ {Tg}°C and Er ≈ {Er} MPa, incorporating {Group1} and {Group2} groups.",
  "Generate a TSMP formulation with Tg = {Tg}°C and Er = {Er} MPa, using monomers with {Group1} and {Group2} functionalities.",
  "Propose a thermoset system achieving Tg = {Tg}°C and Er = {Er} MPa through {Group1} and {Group2} group crosslinking.",
  "Develop a polymer pair with Tg around {Tg}°C and Er near {Er} MPa, featuring {Group1} and {Group2} functional groups.",
  "Generate a TSMP with Tg = {Tg}°C and Er = {Er}Mpa, using functional groups {Group1} and {Group2}.",
  "Design a polymer system with Tg ≈ {Tg}°C and Er ≈ {Er}Mpa that contains {Group1} and {Group2} groups.",
  "Suggest two monomers with  Tg {Tg}°C and Er {Er}Mpa for {Group1} and {Group2} functionalities.",
  "I need a TSMP with Tg = {Tg}°C, Er = {Er}Mpa, and it must include {Group1} and {Group2} groups.",
  "Propose monomers for Tg {Tg}°C and Er {Er}Mpa that are based on {Group1} and {Group2} functionalities."
]

assistant_prompt_template_for_property = [
  "Sure! Here's a TSMP that matches your request:\nMonomer 1: {Monomer1}\nMonomer 2: {Monomer2}",
  
  "Based on your requirements, I suggest the following monomers:\nMonomer 1: {Monomer1}\nMonomer 2: {Monomer2}",
  
  "Great choice of properties and groups. Here's a compatible monomer pair:\nMonomer 1: {Monomer1}\nMonomer 2: {Monomer2}",
  
  "Here is a TSMP designed for Tg ≈ {Tg}°C and Er ≈ {Er}Mpa:\nMonomer 1: {Monomer1}\nMonomer 2: {Monomer2}",
  
  "To achieve Tg of {Tg}°C and Er of {Er}Mpa, consider this monomer combination:\nMonomer 1: {Monomer1}\nMonomer 2: {Monomer2}",
]
  
assistant_prompt_template_for_group=[ "A TSMP with {Group1} and {Group2} groups could be made using:\nMonomer 1: {Monomer1}\nMonomer 2: {Monomer2}",
  
  "Here's a pair of monomers containing {Group1} and {Group2} groups, ideal for TSMP design:\nMonomer 1: {Monomer1}\nMonomer 2: {Monomer2}",
  "Here's a TSMP that includes the requested functional groups:\nMonomer 1 (contains {Group1}): {Monomer1}\nMonomer 2 (contains {Group2}): {Monomer2}",
  
  "Based on your input, I designed monomers with the specified functionalities:\nMonomer 1 with {Group1}: {Monomer1}\nMonomer 2 with {Group2}: {Monomer2}",
  
  "Sure! Here's a monomer pair incorporating {Group1} and {Group2} groups for potential TSMP formation:\nMonomer 1: {Monomer1}\nMonomer 2: {Monomer2}",
  
  "The following monomers feature your desired functional groups and are suitable for crosslinking:\nMonomer 1 ({Group1}): {Monomer1}\nMonomer 2 ({Group2}): {Monomer2}",
  
  "Here is a group-compliant monomer pair:\nMonomer 1 includes {Group1} groups: {Monomer1}\nMonomer 2 includes {Group2} groups: {Monomer2}",
  
  "To meet the functional group constraints of {Group1} and {Group2}, I suggest this combination:\nMonomer 1: {Monomer1}\nMonomer 2: {Monomer2}",
  
  "These monomers match the required group profile:\n- {Group1} in Monomer 1: {Monomer1}\n- {Group2} in Monomer 2: {Monomer2}",
  ]

assistant_prompt_template_for_mix=[
  "I've selected monomers containing the specified reactive groups for your polymer system:\nMonomer 1 ({Group1}): {Monomer1}\nMonomer 2 ({Group2}): {Monomer2}",
  
  "Here's a valid monomer pair designed with the required functionalities:\nMonomer 1 (rich in {Group1}): {Monomer1}\nMonomer 2 (rich in {Group2}): {Monomer2}",
  
  "This monomer pair includes more than two instances of each group as requested:\nMonomer 1 ({Group1} groups): {Monomer1}\nMonomer 2 ({Group2} groups): {Monomer2}"

  "You asked for a TSMP with Tg = {Tg}°C and Er = {Er}Mpa, using {Group1} and {Group2}. Here's a possible combination:\nMonomer 1: {Monomer1}\nMonomer 2: {Monomer2}",
  
  "For the target properties Tg ≈ {Tg}°C and Er ≈ {Er}Mpa, with functional groups {Group1} and {Group2}, try:\nMonomer 1: {Monomer1}\nMonomer 2: {Monomer2}",
  
  "Here's a pair of monomers fulfilling the criteria of Tg = {Tg}°C, Er = {Er}Mpa, and containing {Group1}/{Group2} groups:\nMonomer 1: {Monomer1}\nMonomer 2: {Monomer2}",
]



USER_PROPERTY_PROMPT = [
  "Generate a thermoset shape memory polymer with Tg = {Tg}°C and Er = {Er} MPa.",
    "Design a TSMP with a glass transition temperature of {Tg}°C and an recovery stress of {Er} MPa.",
    "Suggest a polymer system for Tg ≈ {Tg}°C and Er ≈ {Er} MPa.",
    "Propose two monomers that form a TSMP with Tg = {Tg}°C and Er = {Er} MPa.",
    "Create a thermoset polymer with Tg around {Tg}°C and Er near {Er} MPa."
]

USER_GROUP_PROMPT = [
    "Create a monomer pair for TSMPs where one contains {Group1} groups and the other contains {Group2} groups.",
    "Design a thermoset shape memory polymer using monomers that include {Group1} and {Group2} functionalities.",
    "Generate two monomers for a TSMP, ensuring one includes {Group1} groups and the other includes {Group2} groups.",
    "Suggest a TSMP system with one monomer having {Group1} groups and the other featuring {Group2} groups.",
    "Provide a pair of monomers suitable for TSMPs, one rich in {Group1} and the other in {Group2} groups."
]

MIX_PROMPT = ["Generate a TSMP with Tg = {Tg}°C and Er = {Er} MPa, using functional groups {Group1} and {Group2}.",
    "Design a shape memory polymer with Tg ≈ {Tg}°C and Er ≈ {Er} MPa that includes {Group1} and {Group2} groups.",
    "Suggest a TSMP system that satisfies Tg = {Tg}°C and Er = {Er} MPa, incorporating {Group1} and {Group2} functionalities.",
    "Create a thermoset polymer with Tg = {Tg}°C, Er = {Er} MPa, and monomers featuring {Group1} and {Group2} groups.",
    "Propose two monomers that form a TSMP with Tg around {Tg}°C, Er near {Er} MPa, and containing {Group1} and {Group2} groups."]


conversational_tsmp_templates = [
    "Can you help me design a thermoset shape memory polymer?",
    "I need a TSMP - what monomers would you recommend?",
    "Could you suggest a good monomer pair for making a TSMP?",
    "Hey, I'm looking to make a thermoset shape memory polymer - any ideas?",
    "What would be a good TSMP combination for my project?",
    "I'd like to create a shape memory polymer - can you recommend some monomers?",
    "Would you mind helping me put together a TSMP system?",
    "I'm working on a thermoset shape memory polymer - what should I use?",
    "Can you come up with a TSMP design for me?",
    "What monomers would work well for a shape memory polymer?"
]

preference_prompt_templates = [
    "Would you like to design your TSMP based on specific functional groups or target properties?",
    "Should we focus on particular chemical groups or physical properties for your TSMP?",
    "What's more important for your TSMP - certain functional groups or specific properties like Tg and Er?",
    "Do you have any preference - working with specific chemical groups or targeting certain properties?",
    "For your TSMP, are you more interested in the chemistry (functional groups) or the properties (Tg/Er)?",
    "What matters most for your TSMP design - the functional groups we use or the final properties?",
    "Would you rather start with specific chemical groups or target properties for your TSMP?",
    "Are you looking to use particular functional groups, or do you have specific properties in mind?",
    "Should we design your TSMP around certain chemical groups, or focus on achieving specific properties?",
    "What's your priority for the TSMP - working with specific groups or meeting certain property targets?"
]

group_preference_responses = [
    "Let's work with specific functional groups for this TSMP.",
    "I'd like to focus on the chemical groups approach.",
    "Let's design it based on functional groups.",
    "I prefer to work with specific chemical groups.",
    "Let's go with the functional group approach.",
    "I want to focus on the chemistry side - functional groups.",
    "Chemical groups would be better for my needs.",
    "I'd rather work with specific functional groups.",
    "Let's design around chemical functionalities.",
    "The functional group approach sounds good to me.",
    "I think focusing on chemical groups would work best.",
    "Let's start with specific functional groups.",
    "I'd prefer to work with the chemical groups.",
    "Going with functional groups makes more sense for me.",
    "Let's take the chemical group-based approach."
]

property_preference_responses = [
    "I'd rather focus on specific properties.",
    "Let's target particular Tg and Er values.",
    "I prefer to work with property targets.",
    "Properties are more important for my application.",
    "Let's design based on specific properties.",
    "I want to focus on achieving certain properties.",
    "The property-based approach would work better.",
    "I'd like to target specific thermal and mechanical properties.",
    "Let's work towards particular property values.",
    "I prefer to focus on the final properties.",
    "Properties are what matter most for my needs.",
    "Let's design with specific property targets in mind.",
    "I'd rather focus on Tg and Er requirements.",
    "The property-based design would be more helpful.",
    "Let's go with specific property targets."
]

group_selection_templates = [
    "Which functional groups would you like to use? Some options are: vinyl (C=C), imine (C=N), epoxy (C1OC1). Note that not all groups may be available.",
    
    "Please choose your preferred functional groups. For example: vinyl (C=C), imine (C=N), or epoxy (C1OC1). Keep in mind our database might have limitations.",
    
    "What chemical groups interest you? We have options like vinyl (C=C), imine (C=N), and epoxy (C1OC1), though availability may vary.",
    
    "Could you specify which functional groups you want? Examples include vinyl (C=C), imine (C=N), epoxy (C1OC1). Some groups might not be in our database.",
    
    "Which chemical functionalities would you prefer? Some common ones are vinyl (C=C), imine (C=N), and epoxy (C1OC1). Note that options may be limited.",
    
    "Let me know which groups you'd like to work with. We often use vinyl (C=C), imine (C=N), or epoxy (C1OC1), but please note our database isn't exhaustive.",
    
    "What type of functional groups are you looking for? I can work with groups like vinyl (C=C), imine (C=N), epoxy (C1OC1), though some might not be available.",
    
    "Pick your preferred functional groups - for instance, vinyl (C=C), imine (C=N), or epoxy (C1OC1). Just note that not all groups may be in our dataset.",
    
    "Which chemical groups should we use? Common examples include vinyl (C=C), imine (C=N), and epoxy (C1OC1). Keep in mind we might have limited options.",
    
    "Tell me the functional groups you're interested in using. Some possibilities are vinyl (C=C), imine (C=N), epoxy (C1OC1), but availability may vary."
]

property_specification_templates = [
    "I'll need two key properties to design your TSMP: the glass transition temperature (Tg) and stress recovery (Er). What values would you like?",
    
    "To create your TSMP, I need to know your target Tg (glass transition temperature) and Er (stress recovery). Could you specify these?",
    
    "What Tg and Er values are you aiming for? These two properties (glass transition temperature and stress recovery) will guide the design.",
    
    "Let's get specific about the properties - what glass transition temperature (Tg) and stress recovery (Er) do you need?",
    
    "Your TSMP will be designed around two properties: Tg (glass transition temperature) and Er (stress recovery). What values should we target?",
    
    "Could you tell me your desired glass transition temperature (Tg) and stress recovery (Er)? These are the two properties I'll work with.",
    
    "What are your target values for Tg and Er? These two properties (glass transition temp and stress recovery) are essential for the design.",
    
    "I design TSMPs based on two key properties: glass transition temperature (Tg) and stress recovery (Er). What values do you need?",
    
    "Please specify your required Tg (glass transition temperature) and Er (stress recovery) - these are the two properties I'll use.",
    
    "To proceed with the design, I need your target values for glass transition temperature (Tg) and stress recovery (Er).",
    
    "What glass transition temperature (Tg) and stress recovery (Er) would work best for your application? These are the two properties I can work with.",
    
    "I'll customize your TSMP based on two properties: Tg and Er. What values would you like for the glass transition temperature and stress recovery?",
    
    "Could you share your desired values for Tg (glass transition temp) and Er (stress recovery)? These are the two properties we'll use.",
    
    "For your TSMP design, I need two specific properties: the glass transition temperature (Tg) and stress recovery (Er). What values are you looking for?",
    
    "Let's define your TSMP through two key properties - what glass transition temperature (Tg) and stress recovery (Er) should we aim for?"
]


both_preference_responses = [
    "I want a TSMP with both specific groups and target properties in mind.",
    "I'd like to specify both the chemical groups and the properties I need.",
    "Let's design it with both particular functional groups and specific property values.",
    "I want to use certain chemical groups and achieve specific Tg and Er values.",
    "I have both functional groups and property targets in mind for the TSMP.",
    "I'd prefer to specify both the chemistry and the properties we need.",
    "Let's work with both specific groups and target property values.",
    "I want to design using particular groups while hitting certain property targets.",
    "I have requirements for both the chemical groups and the properties.",
    "Let's use specific functional groups and aim for particular Tg and Er values.",
    "I want to combine specific chemical groups with target property values.",
    "I'd like to work with both chosen groups and defined properties.",
    "Let's create a TSMP with specific groups and property requirements.",
    "I want to use particular functional groups and achieve certain properties.",
    "I have preferences for both the chemistry and property targets."
]

both_options_explanation_templates = [
    "I can design TSMPs using various functional groups (like epoxy (C1OC1), imine (NC), vinyl (C=C), thiol (CCS)) and two key properties: glass transition temperature (Tg) and stress recovery (Er).",
    
    "For your TSMP, I can work with different functional groups including epoxy (C1OC1), imine (NC), vinyl (C=C), and thiol (CCS), while targeting specific Tg and Er values.",
    
    "I can help design using common functional groups such as epoxy (C1OC1), imine (NC), vinyl (C=C), or thiol (CCS), along with specific Tg and Er properties.",
    
    "The design can incorporate functional groups like epoxy (C1OC1), imine (NC), vinyl (C=C), or thiol (CCS), and we'll target your desired Tg and Er values.",
    
    "We can work with several functional groups (epoxy (C1OC1), imine (NC), vinyl (C=C), thiol (CCS)) and specify two key properties: Tg and Er.",
    
    "I can create TSMPs using functional groups such as epoxy (C1OC1), imine (NC), vinyl (C=C), or thiol (CCS), while meeting specific Tg and Er targets.",
    
    "The TSMP can be designed with various groups (epoxy (C1OC1), imine (NC), vinyl (C=C), thiol (CCS)) and customized for particular Tg and Er values.",
    
    "We can use different functional groups - epoxy (C1OC1), imine (NC), vinyl (C=C), or thiol (CCS) - and specify the desired Tg and Er properties.",
    
    "I can help you design with functional groups like epoxy (C1OC1), imine (NC), vinyl (C=C), or thiol (CCS), plus target specific Tg and Er values.",
    
    "The system can work with various groups (epoxy (C1OC1), imine (NC), vinyl (C=C), thiol (CCS)) and be optimized for your target Tg and Er.",
    
    "We can incorporate functional groups such as epoxy (C1OC1), imine (NC), vinyl (C=C), or thiol (CCS), while achieving your desired Tg and Er specifications.",
    
    "I can design using common groups like epoxy (C1OC1), imine (NC), vinyl (C=C), or thiol (CCS), and meet specific Tg and Er requirements.",
    
    "The TSMP can be created with functional groups (epoxy (C1OC1), imine (NC), vinyl (C=C), thiol (CCS)) and tailored to your Tg and Er needs.",
    
    "We can work with any of these groups: epoxy (C1OC1), imine (NC), vinyl (C=C), or thiol (CCS), while targeting your specific Tg and Er values.",
    
    "I can help design TSMPs using available groups (epoxy (C1OC1), imine (NC), vinyl (C=C), thiol (CCS)) and optimize for your target Tg and Er properties."
]


# import re

# def extract_monomers2(text):
#     # More flexible pattern that handles various formatting
#     pattern = r"""
#     (?:Monomer\s*1\s*(?:\(.*?\))?\s*:[ \t]*)([\w\s@+\-\[\]\(\)=#$\\/%.,{}'"`]+?)
#     (?:\s*(?:and|,|\n)\s*Monomer\s*2|Monomer\s*2)
#     (?:\(.*?\))?\s*:[ \t]*([\w\s@+\-\[\]\(\)=#$\\/%.,{}'"`]+)
#     """
    
#     match = re.search(pattern, text, re.VERBOSE | re.IGNORECASE | re.DOTALL)
    
#     if match:
#         # Clean up extracted monomers by removing extra whitespace
#         mon1 = match.group(1).strip()
#         mon2 = match.group(2).strip()
#         return mon1, mon2
#     return None, None

# # Test cases
# test_cases = [
#     "Monomer 1: C=C(C=O) and Monomer 2: C=C",
#     "Monomer 1 (vinyl): CH2=CH-COO-CH3\nMonomer 2 (epoxy): C1OC1-CH2",
#     "Monomer 1: includes C=C(C=O) and Monomer 2: includes C=C",
#     "Monomer 1: C@4.3-[CH2]n-OH, Monomer 2: NH2-CH2-CH2-NH2",
#     """Monomer 1: complex structure with (C=O)
#     Monomer 2: another structure with [NH2]"""
# ]

# # Uncomment to test
# for test in test_cases:
#    mon1, mon2 = extract_monomers2(test)
#    print(f"\nInput: {test}")
#    print(f"Extracted: \nMonomer 1: {mon1}\nMonomer 2: {mon2}")


TEST_USER_GROUP_PROMPT = [
    "Design a thermoset shape memory polymer using monomers that include {Group1} in monomer1 and {Group2} in monomer2.",
    "Generate two monomers for a TSMP, ensuring one includes {Group1} in monomer1 and the other includes {Group2} in monomer2.",
    "Suggest a TSMP system with one monomer having {Group1} in monomer1 and the other featuring {Group2} in monomer2.",
]

TEST_USER_PROPERTY_PROMPT = [
  "Generate a thermoset shape memory polymer with Tg = {Tg}°C and Er = {Er} MPa.",
    "Design a TSMP with a glass transition temperature of {Tg}°C and an recovery stress of {Er} MPa.",
    "Suggest a polymer system for Tg ≈ {Tg}°C and Er ≈ {Er} MPa.",
]
TEST_MIX_PROMPT = ["Generate a TSMP with Tg = {Tg}°C and Er = {Er} MPa, using functional groups {Group1} and {Group2}.",
    "Design a shape memory polymer with Tg ≈ {Tg}°C and Er ≈ {Er} MPa that includes {Group1} and {Group2} groups.",
    "Suggest a TSMP system that satisfies Tg = {Tg}°C and Er = {Er} MPa, incorporating {Group1} and {Group2} functionalities.",
    "Create a thermoset polymer with Tg = {Tg}°C, Er = {Er} MPa, and monomers featuring {Group1} in monomer1 and {Group2} in monomer2 groups.",
    "Propose two monomers that form a TSMP with Tg around {Tg}°C, Er near {Er} MPa, and containing {Group1} in monomer1 and {Group2} in monomer2 groups."]


TEST_PROPERTIES = [
  {
    "Tg": 100,
    "Er": 40,
    "Group1": "epoxy(C1OC1)",
    "Group2": "imine(NC)"
  },
  {
    "Tg": 150,
    "Er": 30,
    "Group1": "vinyl(C=C)",
    "Group2": "thiol(CCS)"
  },
  {
    "Tg": 200,
    "Er": 27,
    "Group1": "vinyl(C=C)",
    "Group2": "vinyl(C=C)"
  },
  {
    "Tg": 100,
    "Er": 100,
    "Group1": "acrylate(C=C(C=O))",
    "Group2": "vinyl(C=C)"
  },
   {
    "Tg": 50,
    "Er": 20,
    "Group1": "vinyl(C=C)",
    "Group2": "hydroxyl(=O)"
  }

]

