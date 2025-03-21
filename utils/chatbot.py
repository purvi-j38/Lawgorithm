import re
from typing import List, Dict, Any, Optional

class LegalChatbot:
    """
    A rule-based chatbot that can answer questions about Indian legal documents.
    This is a simplified implementation that would ideally be replaced with a proper LLM.
    """
    
    def __init__(self):
        # Load pre-defined responses
        self.responses = self._load_responses()
        
        # Store conversation history
        self.conversation_history = []
        
        # Current document context
        self.current_document = None
    
    def _load_responses(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load predefined response patterns and templates."""
        return {
            "greetings": [
                {"pattern": r"(hi|hello|hey|greetings)", 
                 "response": "Hello! I'm your Indian legal assistant. How can I help you today?"},
            ],
            "document_info": [
                {"pattern": r"what('s| is) (this|the) document (about|talking about|containing|saying)",
                 "response": "This document appears to be {doc_type}. It contains references to {legal_refs}. The key entities mentioned are {entities}."},
                {"pattern": r"(summarize|summary|describe|explain) (the|this) document",
                 "response": "Here's a brief summary of the document: {summary}"},
            ],
            "legal_terms": [
                {"pattern": r"what (does|is|are) (.*?) (mean|means|refer to|referring to)",
                 "response": "The term '{term}' in Indian legal context typically refers to {term_definition}. Would you like me to explain it further?"},
                {"pattern": r"explain (the term|the legal term|legal term) (.*)",
                 "response": "In Indian law, '{term}' means {term_definition}."},
            ],
            "legal_advice": [
                {"pattern": r"(can|should|would|will|do) I (need to|have to|must) (.*?)",
                 "response": "I cannot provide personalized legal advice. For specific guidance on {issue}, please consult a qualified advocate."},
                {"pattern": r"(what are my|my) (rights|obligations|duties) (in|under|for|when) (.*?)",
                 "response": "Questions about specific rights and obligations require personalized legal advice. For matters related to {context}, please consult a qualified legal professional."},
            ],
            "precedent_cases": [
                {"pattern": r"(similar|precedent|previous|related) cases",
                 "response": "Some relevant precedent cases for this matter include: {precedents}. Would you like more details on any of these cases?"},
                {"pattern": r"(case law|jurisprudence|legal precedent) (for|on|related to) (.*?)",
                 "response": "The Indian jurisprudence on {topic} includes these key cases: {precedents}."},
            ],
            "indian_specific": [
                {"pattern": r"(IPC|Indian Penal Code) (section|sec\.|s\.) (\d+)",
                 "response": "Section {section} of the Indian Penal Code deals with {ipc_section_info}."},
                {"pattern": r"(CrPC|Criminal Procedure Code) (section|sec\.|s\.) (\d+)",
                 "response": "Section {section} of the Criminal Procedure Code relates to {crpc_section_info}."},
                {"pattern": r"(CPC|Civil Procedure Code) (section|sec\.|s\.) (\d+)",
                 "response": "Section {section} of the Civil Procedure Code covers {cpc_section_info}."},
                {"pattern": r"(article|a\.) (\d+) (of|in) (the|our|indian) constitution",
                 "response": "Article {article} of the Indian Constitution establishes {constitution_article_info}."},
            ],
            "fallback": [
                {"response": "I'm still learning about Indian law. Could you please rephrase your question or ask something more specific about this legal document?"},
                {"response": "I'm not sure I understand your question in the context of Indian law. Could you try asking in a different way?"},
                {"response": "As a legal assistant focused on Indian law, I'm still developing my knowledge. Could you ask something more specific about the document?"}
            ]
        }
    
    def set_document_context(self, document: Any) -> None:
        """Set the current document context for the chatbot."""
        self.current_document = document
    
    def get_response(self, query: str) -> str:
        """
        Generate a response to a user query based on patterns and document context.
        
        Args:
            query (str): The user's question or input
            
        Returns:
            str: The chatbot's response
        """
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": query})
        
        # Clean the query
        clean_query = query.lower().strip()
        
        # Check each category of responses
        for category, patterns in self.responses.items():
            if category == "fallback":
                continue
                
            for pattern_dict in patterns:
                pattern = pattern_dict["pattern"]
                match = re.search(pattern, clean_query)
                
                if match:
                    # Get the response template
                    response_template = pattern_dict["response"]
                    
                    # Fill in any placeholders with context-specific information
                    filled_response = self._fill_response_template(response_template, match, category)
                    
                    # Add to conversation history
                    self.conversation_history.append({"role": "assistant", "content": filled_response})
                    return filled_response
        
        # If no patterns matched, use a fallback response
        import random
        fallback = random.choice(self.responses["fallback"])
        fallback_response = fallback["response"]
        
        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": fallback_response})
        return fallback_response
    
    def _fill_response_template(self, template: str, match: re.Match, category: str) -> str:
        """
        Fill in placeholders in response templates with context-specific information.
        
        Args:
            template (str): The response template with placeholders
            match (re.Match): The regex match object
            category (str): The category of the response
            
        Returns:
            str: The filled response
        """
        # Get document context
        doc = self.current_document
        
        # Replace common placeholders
        if "{term}" in template:
            term = match.group(2).strip() if len(match.groups()) >= 2 else "the term"
            template = template.replace("{term}", term)
            
        if "{term_definition}" in template:
            term = match.group(2).strip() if len(match.groups()) >= 2 else ""
            definition = self._get_term_definition(term)
            template = template.replace("{term_definition}", definition)
            
        if "{issue}" in template:
            issue = match.group(3).strip() if len(match.groups()) >= 3 else "this legal matter"
            template = template.replace("{issue}", issue)
            
        if "{context}" in template:
            context = match.group(4).strip() if len(match.groups()) >= 4 else "this specific situation"
            template = template.replace("{context}", context)
            
        if "{topic}" in template:
            topic = match.group(3).strip() if len(match.groups()) >= 3 else "this legal topic"
            template = template.replace("{topic}", topic)
        
        # Document-specific placeholders
        if doc:
            if "{doc_type}" in template:
                doc_type = "a legal document" if not hasattr(doc, "doc_type") else doc.doc_type
                template = template.replace("{doc_type}", doc_type)
                
            if "{summary}" in template:
                summary = "No summary available" if not hasattr(doc, "summary") else (doc.summary or "No summary available")
                template = template.replace("{summary}", summary)
                
            if "{legal_refs}" in template:
                refs = self._extract_legal_references()
                template = template.replace("{legal_refs}", refs)
                
            if "{entities}" in template:
                entities = self._extract_entities()
                template = template.replace("{entities}", entities)
                
            if "{precedents}" in template:
                precedents = self._extract_precedents()
                template = template.replace("{precedents}", precedents)
                
        # Handle Indian-specific placeholders
        if "{section}" in template and category == "indian_specific":
            section = match.group(3).strip() if len(match.groups()) >= 3 else "the section"
            template = template.replace("{section}", section)
            
        if "{ipc_section_info}" in template:
            section = match.group(3).strip() if len(match.groups()) >= 3 else ""
            info = self._get_ipc_section_info(section)
            template = template.replace("{ipc_section_info}", info)
            
        if "{crpc_section_info}" in template:
            section = match.group(3).strip() if len(match.groups()) >= 3 else ""
            info = self._get_crpc_section_info(section)
            template = template.replace("{crpc_section_info}", info)
            
        if "{cpc_section_info}" in template:
            section = match.group(3).strip() if len(match.groups()) >= 3 else ""
            info = self._get_cpc_section_info(section)
            template = template.replace("{cpc_section_info}", info)
            
        if "{article}" in template:
            article = match.group(2).strip() if len(match.groups()) >= 2 else "the article"
            template = template.replace("{article}", article)
            
        if "{constitution_article_info}" in template:
            article = match.group(2).strip() if len(match.groups()) >= 2 else ""
            info = self._get_constitution_article_info(article)
            template = template.replace("{constitution_article_info}", info)
            
        return template
    
    def _get_term_definition(self, term: str) -> str:
        """Get the definition of a legal term."""
        # Dictionary of common Indian legal terms
        indian_legal_terms = {
            "writ petition": "a court petition for extraordinary review, seeking justice when fundamental rights are violated",
            "suo motu": "action taken by a court on its own initiative without any party requesting it",
            "cognizance": "formal recognition by a court that it has the power to deal with a particular case or matter",
            "vakalatnama": "document by which a litigant authorizes an advocate to represent them in court",
            "lok adalat": "people's court where disputes are settled through compromise and conciliation",
            "habeas corpus": "legal remedy ensuring a person under arrest is brought before a court",
            "caveat": "a notice given by someone that they have an interest in the matter and should be informed before action is taken",
            "anticipatory bail": "bail granted to a person who anticipates arrest for a non-bailable offense",
            "fir": "First Information Report, the document prepared by police when they receive information about a cognizable offense",
            "ipc": "Indian Penal Code, the main criminal code of India",
            "cpc": "Code of Civil Procedure, the procedural law related to civil proceedings in India",
            "crpc": "Code of Criminal Procedure, the main legislation on procedure for administration of criminal law in India",
            "pil": "Public Interest Litigation, court case filed to protect the public interest",
            # Additional terms
            "high court": "one of the constitutional courts in India, with jurisdiction over a state or union territory",
            "supreme court": "the highest judicial forum and final court of appeal in India",
            "advocate": "a legal professional qualified to represent clients in Indian courts",
            "affidavit": "a written statement confirmed by oath or affirmation for use as evidence in court",
            "bail": "temporary release of an accused person awaiting trial, sometimes on condition of a security deposit",
            "contempt of court": "disobedience to or disrespect towards a court of law and its officers",
            "jurisdiction": "the official power to make legal decisions and judgments",
            "plaintiff": "a person who brings a case against another in a court of law",
            "defendant": "an individual, company, or institution sued or accused in a court of law",
            "respondent": "a person who answers or replies to a petition, especially in certain legal proceedings",
            "petitioner": "a person who presents a petition to a court or other official body",
            "ex parte": "a legal proceeding brought by one person in the absence of another",
            "adjournment": "postponement of proceedings to another date or time",
            "injunction": "a judicial order restraining a person from beginning or continuing an action"
        }
        
        # Normalize the term for lookup
        term_lower = term.lower().strip()
        
        # If term exists in our dictionary
        if term_lower in indian_legal_terms:
            return indian_legal_terms[term_lower]
        
        # For compound terms, try to match parts
        for known_term, definition in indian_legal_terms.items():
            if known_term in term_lower or term_lower in known_term:
                return definition
        
        # Default response
        return "a legal concept in Indian jurisprudence that may require specific expertise to interpret correctly"
    
    def _extract_legal_references(self) -> str:
        """Extract legal references from the current document."""
        # In a real implementation, this would analyze the document
        if not self.current_document or not hasattr(self.current_document, "content"):
            return "various legal provisions"
            
        # Very simple extraction for demonstration
        content = self.current_document.content
        references = []
        
        # Check for common Indian legal references
        if re.search(r'(IPC|Indian Penal Code)', content):
            references.append("the Indian Penal Code")
        if re.search(r'(CrPC|Criminal Procedure Code)', content):
            references.append("the Criminal Procedure Code")
        if re.search(r'(CPC|Civil Procedure Code)', content):
            references.append("the Civil Procedure Code")
        if re.search(r'(Constitution of India|Indian Constitution)', content):
            references.append("the Constitution of India")
            
        if not references:
            # Check for generic references
            if re.search(r'(Section|Sec\.|S\.) \d+', content):
                references.append("various statutory provisions")
            if re.search(r'v\.', content):
                references.append("case precedents")
                
        if not references:
            return "legal principles and statutes"
            
        return ", ".join(references)
    
    def _extract_entities(self) -> str:
        """Extract key entities from the current document."""
        # In a real implementation, this would use NER on the document
        if not self.current_document:
            return "various parties and organizations"
            
        # For demonstration, return placeholder text
        return "individuals, organizations, and institutions relevant to the case"
    
    def _extract_precedents(self) -> str:
        """Extract precedent cases from the current document."""
        # In a real implementation, this would analyze the document for case citations
        if not self.current_document:
            return "relevant Indian case law"
            
        # For demonstration, return placeholder text
        precedents = [
            "State of Punjab v. Baldev Singh",
            "Kesavananda Bharati v. State of Kerala",
            "M.C. Mehta v. Union of India"
        ]
        
        return ", ".join(precedents)
    
    def _get_ipc_section_info(self, section: str) -> str:
        """Get information about a section of the Indian Penal Code."""
        # Dictionary of some common IPC sections
        ipc_sections = {
            "299": "culpable homicide",
            "300": "murder",
            "302": "punishment for murder",
            "304": "culpable homicide not amounting to murder",
            "307": "attempt to murder",
            "319": "hurt",
            "320": "grievous hurt",
            "339": "wrongful restraint",
            "340": "wrongful confinement",
            "378": "theft",
            "383": "extortion",
            "390": "robbery",
            "391": "dacoity",
            "405": "criminal breach of trust",
            "415": "cheating",
            "441": "criminal trespass",
            "499": "defamation",
            "503": "criminal intimidation"
        }
        
        if section in ipc_sections:
            return ipc_sections[section]
        return "a specific criminal offense under Indian law"
    
    def _get_crpc_section_info(self, section: str) -> str:
        """Get information about a section of the Criminal Procedure Code."""
        # Dictionary of some common CrPC sections
        crpc_sections = {
            "41": "when police may arrest without warrant",
            "50": "informing person arrested about grounds of arrest",
            "54": "examination of arrested person by medical officer",
            "91": "summons to produce document or other thing",
            "125": "order for maintenance of wives, children and parents",
            "154": "information in cognizable cases",
            "161": "examination of witnesses by police",
            "164": "recording of confessions and statements",
            "190": "cognizance of offences by Magistrates",
            "202": "postponement of issue of process",
            "204": "issue of process",
            "207": "supply of documents to accused",
            "226": "opening case for prosecution",
            "228": "framing of charge",
            "262": "procedure for summary trials",
            "304": "legal aid to accused",
            "306": "tender of pardon to accomplice",
            "357": "order to pay compensation",
            "436": "provisions of bail",
            "438": "direction for grant of bail to person apprehending arrest",
            "439": "special powers of High Court or Court of Session regarding bail"
        }
        
        if section in crpc_sections:
            return crpc_sections[section]
        return "criminal procedure under Indian law"
    
    def _get_cpc_section_info(self, section: str) -> str:
        """Get information about a section of the Civil Procedure Code."""
        # Dictionary of some common CPC sections
        cpc_sections = {
            "9": "courts' jurisdiction to try all civil suits",
            "10": "stay of suit",
            "11": "res judicata",
            "13": "foreign judgments",
            "20": "suits to be instituted where subject matter situate",
            "35": "costs",
            "51": "powers of court to enforce execution",
            "75": "power of court to issue commissions",
            "80": "notice before suit against government",
            "89": "settlement of disputes outside the Court",
            "100": "second appeal",
            "115": "revision",
            "144": "application for restitution",
            "151": "inherent powers of court"
        }
        
        if section in cpc_sections:
            return cpc_sections[section]
        return "civil procedure under Indian law"
    
    def _get_constitution_article_info(self, article: str) -> str:
        """Get information about an article of the Indian Constitution."""
        # Dictionary of some important constitutional articles
        constitution_articles = {
            "12": "definition of the State",
            "13": "laws inconsistent with fundamental rights",
            "14": "equality before law",
            "15": "prohibition of discrimination",
            "16": "equality of opportunity in public employment",
            "19": "protection of certain rights regarding freedom of speech, etc.",
            "20": "protection in respect of conviction for offences",
            "21": "protection of life and personal liberty",
            "22": "protection against arrest and detention",
            "25": "freedom of conscience and free profession, practice and propagation of religion",
            "32": "remedies for enforcement of rights",
            "44": "uniform civil code for citizens",
            "51": "promotion of international peace and security",
            "72": "power of President to grant pardons",
            "143": "power of President to consult Supreme Court",
            "226": "power of High Courts to issue certain writs",
            "245": "extent of laws made by Parliament and by the Legislatures of States",
            "356": "provisions in case of failure of constitutional machinery in States",
            "368": "power of Parliament to amend the Constitution"
        }
        
        if article in constitution_articles:
            return constitution_articles[article]
        return "a provision in the Indian Constitution"
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history."""
        return self.conversation_history
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []

# Initialize a global instance
legal_chatbot = LegalChatbot()