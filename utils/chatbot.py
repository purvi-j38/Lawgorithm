import re
from typing import Dict, List, Any, Optional
import json
from utils.rag_pipeline import rag_pipeline

class LegalChatbot:
    """
    A rule-based chatbot that can answer questions about Indian legal documents.
    This is a simplified implementation that would ideally be replaced with a proper LLM.
    """
    
    def __init__(self):
        """Initialize the chatbot."""
        self.document_context = None
        self.conversation_history = []
        self._load_responses()
        
    def _load_responses(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load predefined response patterns and templates."""
        # Simplified rule-based responses for common questions
        self.responses = {
            "greeting": [
                {
                    "pattern": r"\b(?:hi|hello|hey|greetings|namaste)\b",
                    "response": "Hello! How can I help you with your legal document or Indian law questions today?"
                }
            ],
            "farewell": [
                {
                    "pattern": r"\b(?:bye|goodbye|see you|farewell|thanks|thank you)\b",
                    "response": "Goodbye! Feel free to ask if you have more questions about Indian law."
                }
            ],
            "document_info": [
                {
                    "pattern": r"what(?:'s| is) this document about",
                    "response": "This document appears to be about {DOCUMENT_SUMMARY}. Is there anything specific you'd like to know about it?"
                },
                {
                    "pattern": r"who(?:'s| is) involved in this (?:case|document)",
                    "response": "Based on the document, key entities involved include: {ENTITIES}"
                }
            ],
            "law_definitions": [
                {
                    "pattern": r"what (?:does|is) ([a-zA-Z\s]+) mean",
                    "response": "The term '{TERM}' in Indian legal context refers to {DEFINITION}. Would you like more information about this term?"
                },
                {
                    "pattern": r"define ([a-zA-Z\s]+)",
                    "response": "In Indian law, '{TERM}' is defined as {DEFINITION}. This is commonly referenced in legal proceedings."
                },
                {
                    "pattern": r"explain ([a-zA-Z\s]+)",
                    "response": "'{TERM}' {DEFINITION}. This concept is important in Indian legal practice."
                }
            ],
            "case_law": [
                {
                    "pattern": r"(?:cases|precedents) similar to",
                    "response": "Some relevant precedents to this case include: {PRECEDENTS}"
                },
                {
                    "pattern": r"landmark cases",
                    "response": "Notable landmark cases in this area of Indian law include: {PRECEDENTS}"
                }
            ],
            "legal_codes": [
                {
                    "pattern": r"section (\d+)(?:A|B|C|D|)? of (IPC|CrPC|CPC)",
                    "response": "Section {SECTION} of {CODE} deals with {SECTION_INFO}. This is relevant to your document because {RELEVANCE}."
                },
                {
                    "pattern": r"article (\d+)(?:A|B|C|D|)? of (?:the )?constitution",
                    "response": "Article {ARTICLE} of the Indian Constitution provides that {ARTICLE_INFO}. In your context, this is relevant because {RELEVANCE}."
                }
            ],
            "fallback": [
                {
                    "pattern": r".*",
                    "response": "I'll look into your question about Indian law. Let me check the document for more information."
                }
            ]
        }
        return self.responses
        
    def set_document_context(self, document: Any) -> None:
        """Set the current document context for the chatbot."""
        self.document_context = document
        # Add document to RAG pipeline if it has an ID and content
        if hasattr(document, 'id') and hasattr(document, 'content'):
            rag_pipeline.add_document(document.id, document.content)
    
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
        
        # Check for specific Indian law queries
        indian_law_response = self._check_indian_law_query(query)
        if indian_law_response:
            self.conversation_history.append({"role": "assistant", "content": indian_law_response})
            return indian_law_response
            
        # Try to generate response using RAG pipeline first
        if self.document_context is not None:
            rag_response, chunks = rag_pipeline.query(query)
            if chunks:  # If we found relevant information in the document
                response = rag_response
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
        
        # Fall back to rule-based responses
        for category, patterns in self.responses.items():
            for pattern_data in patterns:
                match = re.search(pattern_data["pattern"], query, re.IGNORECASE)
                if match:
                    response = self._fill_response_template(pattern_data["response"], match, category)
                    self.conversation_history.append({"role": "assistant", "content": response})
                    return response
        
        # Default fallback with better message
        fallback_response = "I don't have specific information on that Indian law topic. For the hackathon demo, my knowledge is limited. In a production version, I would connect to Indian law databases like IndianKanoon.org to provide accurate responses."
        self.conversation_history.append({"role": "assistant", "content": fallback_response})
        return fallback_response
        
    def _check_indian_law_query(self, query: str) -> Optional[str]:
        """
        Check for specific Indian law queries and provide hardcoded responses for demo purposes.
        In a real system, this would be connected to an actual legal database.
        
        Args:
            query (str): User query
            
        Returns:
            Optional[str]: Response for Indian law query or None
        """
        query_lower = query.lower()
        
        # Check for common IPC queries
        if "section 370" in query_lower or "article 370" in query_lower:
            return ("Article 370 of the Indian Constitution granted special autonomous status to Jammu and Kashmir. "
                   "It was revoked in August 2019 through a Presidential Order and the passage of the Jammu and Kashmir Reorganisation Act.")
        
        if "section 377" in query_lower:
            return ("Section 377 of the Indian Penal Code criminalized 'carnal intercourse against the order of nature'. "
                   "In September 2018, the Supreme Court of India decriminalized consensual homosexual acts by declaring the relevant portions of Section 377 unconstitutional.")
        
        if "section 302" in query_lower:
            return ("Section 302 of the Indian Penal Code deals with punishment for murder. It states: 'Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.'")
        
        if "section 498a" in query_lower:
            return ("Section 498A of the Indian Penal Code deals with husband or relative of husband of a woman subjecting her to cruelty. "
                   "It is a cognizable, non-bailable, and non-compoundable offense, designed to protect women from domestic violence and dowry harassment.")
        
        if "section 144" in query_lower:
            return ("Section 144 of the Criminal Procedure Code (CrPC) empowers a district magistrate to prohibit the assembly of four or more people in an area. "
                   "It is often used to impose restrictions to prevent disturbances of public tranquility.")
        
        # Famous Indian cases
        if "kesavananda bharati" in query_lower:
            return ("Kesavananda Bharati v. State of Kerala (1973) is one of the most important cases in Indian constitutional history. "
                   "The Supreme Court established the 'basic structure doctrine', holding that Parliament cannot amend the basic structure of the Constitution.")
        
        if "vishaka" in query_lower and "sexual harassment" in query_lower:
            return ("Vishaka v. State of Rajasthan (1997) was a landmark case where the Supreme Court laid down guidelines to address sexual harassment at the workplace, "
                   "which later formed the basis for the Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013.")
        
        # Indian Constitution
        if "fundamental rights" in query_lower and "india" in query_lower:
            return ("The Fundamental Rights in the Indian Constitution include: Right to Equality (Articles 14-18), Right to Freedom (Articles 19-22), "
                   "Right against Exploitation (Articles 23-24), Right to Freedom of Religion (Articles 25-28), Cultural and Educational Rights (Articles 29-30), "
                   "and Right to Constitutional Remedies (Article 32).")
        
        if "directive principles" in query_lower:
            return ("The Directive Principles of State Policy in the Indian Constitution (Articles 36-51) are guidelines for the government to establish a just "
                   "social order. While not enforceable in courts, they are fundamental in governance and policymaking.")
        
        # Generic Indian legal system
        if "pil" in query_lower or "public interest litigation" in query_lower:
            return ("Public Interest Litigation (PIL) in India allows any public-spirited person to approach the Supreme Court or High Courts seeking justice "
                   "for those unable to do so themselves. It was introduced in the 1980s and has been instrumental in advancing social justice and human rights in India.")
        
        if "lok adalat" in query_lower:
            return ("Lok Adalat ('People's Court') is an alternative dispute resolution mechanism in India that allows for settlement of cases pending before courts "
                   "through conciliation and compromise. It was established under the Legal Services Authorities Act, 1987.")
            
        return None
    
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
        response = template
        
        # Replace placeholders with appropriate content based on category
        if '{DOCUMENT_SUMMARY}' in response and self.document_context:
            # Provide a basic summary if we have a document
            if hasattr(self.document_context, 'content'):
                content = self.document_context.content
                sentences = content.split('.')[:3]  # First 3 sentences as a simple summary
                summary = '. '.join(sentences) + '.'
                response = response.replace('{DOCUMENT_SUMMARY}', summary)
            else:
                response = response.replace('{DOCUMENT_SUMMARY}', "the legal matter at hand")
        
        if '{ENTITIES}' in response and self.document_context:
            entities = self._extract_entities()
            response = response.replace('{ENTITIES}', entities)
        
        if '{TERM}' in response and match and match.groups():
            term = match.group(1).strip()
            response = response.replace('{TERM}', term)
            definition = self._get_term_definition(term)
            response = response.replace('{DEFINITION}', definition)
        
        if '{PRECEDENTS}' in response and self.document_context:
            precedents = self._extract_precedents()
            response = response.replace('{PRECEDENTS}', precedents)
        
        if '{SECTION}' in response and match and match.groups():
            section = match.group(1)
            response = response.replace('{SECTION}', section)
            
            if '{CODE}' in response and len(match.groups()) > 1:
                code = match.group(2)
                response = response.replace('{CODE}', code)
                
                # Get information about the section based on the code
                if code == 'IPC':
                    section_info = self._get_ipc_section_info(section)
                elif code == 'CrPC':
                    section_info = self._get_crpc_section_info(section)
                elif code == 'CPC':
                    section_info = self._get_cpc_section_info(section)
                else:
                    section_info = "a specific provision in Indian law"
                
                response = response.replace('{SECTION_INFO}', section_info)
        
        if '{ARTICLE}' in response and match and match.groups():
            article = match.group(1)
            response = response.replace('{ARTICLE}', article)
            article_info = self._get_constitution_article_info(article)
            response = response.replace('{ARTICLE_INFO}', article_info)
        
        if '{RELEVANCE}' in response:
            response = response.replace('{RELEVANCE}', "it appears to be connected to the legal issues in this document")
        
        return response
    
    def _get_term_definition(self, term: str) -> str:
        """Get the definition of a legal term."""
        # Simplified dictionary of Indian legal terms
        legal_terms = {
            "writ petition": "a formal written application to a court challenging a decision or action by a public authority, commonly used for constitutional remedies",
            "suo motu": "a Latin phrase which means 'on its own motion', used when a court takes action on its own initiative without any party requesting it",
            "vakalatnama": "a document by which a litigant authorizes an advocate to represent them in court",
            "lok adalat": "people's court where disputes are settled through compromise and conciliation rather than through adversarial litigation",
            "fir": "First Information Report, the document prepared by police when they receive information about a cognizable offense",
            "ipc": "Indian Penal Code, the main criminal code of India enacted in 1860 during the British Raj",
            "cpc": "Code of Civil Procedure, the procedural law related to civil proceedings in India",
            "crpc": "Code of Criminal Procedure, the main legislation on procedure for administration of criminal law in India",
            "pil": "Public Interest Litigation, court case filed to protect the public interest",
            "anticipatory bail": "bail granted to a person who anticipates arrest for a non-bailable offense",
            "cognizable offense": "a type of crime where a police officer can arrest without a warrant and start investigation without court permission",
            "non-cognizable offense": "a type of crime where a police officer has no authority to arrest without warrant and cannot start investigation without court permission",
            "habeas corpus": "a legal recourse whereby a person can report an unlawful detention or imprisonment to a court",
            "mandamus": "a judicial writ issued as a command to an inferior court or ordering a person to perform a public or statutory duty",
            "caveat": "a notice given by someone that they have interest in a case and must be informed before any action on it",
            "interim order": "temporary order issued during the pendency of a suit which remains in force until the final disposal of the suit",
            "advocate": "a legal professional who is qualified to represent clients in Indian courts",
            "affidavit": "a written sworn statement of fact voluntarily made by a person under an oath",
            "bail": "temporary release of an accused person awaiting trial, sometimes on condition that a sum of money is lodged to guarantee their appearance in court",
            "contempt of court": "disobedience to or disrespect for the authority, justice, and dignity of a court",
            "decree": "formal expression of an adjudication which conclusively determines the rights of the parties regarding the matters in controversy in the suit",
            "deponent": "a person who gives evidence in an affidavit",
            "ex parte": "a legal proceeding brought by one person in the absence of another",
            "injunction": "a judicial order restraining a person from beginning or continuing an action that threatens or invades the legal right of another",
            "jurisdiction": "the official power to make legal decisions and judgments",
            "locus standi": "the right or capacity to bring an action or to appear in a court",
            "plaint": "a document filed by the plaintiff initiating a civil suit in a court",
            "stay order": "an order by the court temporarily suspending the proceeding of the case or execution of decree",
            "summons": "a document issued by a court to a defendant informing them of a lawsuit and calling them to answer",
            "tort": "a wrongful act leading to a civil legal liability",
            "witness": "a person who gives testimony under oath in a legal proceeding"
        }
        
        # Check for term in dictionary (case-insensitive)
        term_lower = term.lower()
        if term_lower in legal_terms:
            return legal_terms[term_lower]
        
        # Check for partial matches
        for key, value in legal_terms.items():
            if key in term_lower or term_lower in key:
                return value
        
        return "a specific legal concept in Indian law"
    
    def _extract_legal_references(self) -> str:
        """Extract legal references from the current document."""
        if not self.document_context or not hasattr(self.document_context, 'content'):
            return "various legal provisions"
            
        content = self.document_context.content
        references = []
        
        # Look for IPC sections
        ipc_matches = re.findall(r'section\s+(\d+(?:[A-Z])?)(?:\s+of\s+the\s+Indian\s+Penal\s+Code|\s+IPC)', content, re.IGNORECASE)
        if ipc_matches:
            references.extend([f"Section {m} of IPC" for m in ipc_matches[:3]])
            
        # Look for CrPC sections
        crpc_matches = re.findall(r'section\s+(\d+(?:[A-Z])?)(?:\s+of\s+the\s+Code\s+of\s+Criminal\s+Procedure|\s+CrPC)', content, re.IGNORECASE)
        if crpc_matches:
            references.extend([f"Section {m} of CrPC" for m in crpc_matches[:3]])
            
        # Look for CPC sections
        cpc_matches = re.findall(r'section\s+(\d+(?:[A-Z])?)(?:\s+of\s+the\s+Code\s+of\s+Civil\s+Procedure|\s+CPC)', content, re.IGNORECASE)
        if cpc_matches:
            references.extend([f"Section {m} of CPC" for m in cpc_matches[:3]])
            
        # Look for Constitutional articles
        const_matches = re.findall(r'article\s+(\d+(?:[A-Z])?)(?:\s+of\s+the\s+Constitution)', content, re.IGNORECASE)
        if const_matches:
            references.extend([f"Article {m} of the Constitution" for m in const_matches[:3]])
            
        if not references:
            return "various legal provisions"
            
        return ", ".join(references)
    
    def _extract_entities(self) -> str:
        """Extract key entities from the current document."""
        if not self.document_context or not hasattr(self.document_context, 'content'):
            return "relevant parties in the case"
            
        content = self.document_context.content
        
        # Extract names - simplified approach using regex patterns for Indian names
        # This would ideally use NER models for Indian names
        entities = []
        
        # Look for common patterns of names in legal documents (vs, versus)
        parties_pattern = r'([A-Z][a-zA-Z\s\.]+)\s+(?:v(?:s|s\.)|\bversus\b)\s+([A-Z][a-zA-Z\s\.]+)'
        parties_matches = re.findall(parties_pattern, content)
        if parties_matches:
            for match in parties_matches:
                entities.extend([m.strip() for m in match if m.strip()])
        
        # Look for common designations
        designations = ['petitioner', 'respondent', 'appellant', 'plaintiff', 'defendant', 'accused']
        for designation in designations:
            pattern = rf'(?:the\s+)?([A-Z][a-zA-Z\s\.]+),?\s+the\s+{designation}'
            matches = re.findall(pattern, content, re.IGNORECASE)
            entities.extend([m.strip() for m in matches if m.strip()])
        
        if not entities:
            return "relevant parties in the case"
            
        # Return unique entities
        unique_entities = list(set(entities))
        return ", ".join(unique_entities[:5])  # Return maximum 5 entities
    
    def _extract_precedents(self) -> str:
        """Extract precedent cases from the current document."""
        if not self.document_context or not hasattr(self.document_context, 'content'):
            return "relevant precedent cases in Indian law"
            
        content = self.document_context.content
        
        # Look for case citation patterns (AIR, SCC, SCR, etc.)
        citation_patterns = [
            r'([A-Z][a-zA-Z\s\.]+)\s+v(?:s|\.)\s+([A-Z][a-zA-Z\s\.]+),?\s+\((\d{4})\)\s+(\d+)\s+SCC\s+(\d+)',
            r'([A-Z][a-zA-Z\s\.]+)\s+v(?:s|\.)\s+([A-Z][a-zA-Z\s\.]+),?\s+AIR\s+(\d{4})\s+SC\s+(\d+)',
            r'([A-Z][a-zA-Z\s\.]+)\s+v(?:s|\.)\s+([A-Z][a-zA-Z\s\.]+),?\s+(\d{4})\s+(\d+)\s+SCR\s+(\d+)',
            r'([A-Z][a-zA-Z\s\.]+)\s+v(?:s|\.)\s+([A-Z][a-zA-Z\s\.]+),?\s+(\d{4})',
        ]
        
        precedents = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, content)
            if matches:
                for match in matches:
                    if len(match) >= 3:
                        name1, name2, year = match[0], match[1], match[2]
                        precedents.append(f"{name1.strip()} v. {name2.strip()} ({year})")
        
        if not precedents:
            return "relevant precedent cases in Indian law"
            
        # Return unique precedents
        unique_precedents = list(set(precedents))
        return ", ".join(unique_precedents[:3])  # Return maximum 3 precedents
    
    def _get_ipc_section_info(self, section: str) -> str:
        """Get information about a section of the Indian Penal Code."""
        # Simplified mapping of common IPC sections
        ipc_sections = {
            "299": "culpable homicide, which is causing death with the intention of causing death or bodily injury likely to cause death",
            "300": "murder, which is causing death with the intention of causing death or such bodily injury that the offender knows is likely to cause death",
            "304": "culpable homicide not amounting to murder, which carries a lesser penalty than murder",
            "304A": "causing death by negligence",
            "304B": "dowry death",
            "307": "attempt to murder",
            "309": "attempt to commit suicide",
            "319": "causing hurt",
            "320": "causing grievous hurt",
            "326": "voluntarily causing grievous hurt with dangerous weapons",
            "354": "assault or criminal force to woman with intent to outrage her modesty",
            "375": "rape",
            "376": "punishment for rape",
            "378": "theft",
            "383": "extortion",
            "390": "robbery",
            "391": "dacoity, which is robbery committed by five or more persons",
            "406": "criminal breach of trust",
            "415": "cheating",
            "420": "cheating and dishonestly inducing delivery of property",
            "499": "defamation",
            "503": "criminal intimidation",
            "506": "punishment for criminal intimidation",
            "509": "word, gesture, or act intended to insult the modesty of a woman"
        }
        
        if section in ipc_sections:
            return ipc_sections[section]
        
        return f"a specific provision in the Indian Penal Code"
    
    def _get_crpc_section_info(self, section: str) -> str:
        """Get information about a section of the Criminal Procedure Code."""
        # Simplified mapping of common CrPC sections
        crpc_sections = {
            "41": "when police may arrest without warrant",
            "125": "order for maintenance of wives, children, and parents",
            "144": "power to issue order in urgent cases of nuisance or apprehended danger",
            "154": "information in cognizable cases (FIR)",
            "156": "police officer's power to investigate cognizable cases",
            "157": "procedure for investigation",
            "161": "examination of witnesses by police",
            "164": "recording of confessions and statements",
            "167": "procedure when investigation cannot be completed in twenty-four hours",
            "197": "prosecution of judges and public servants",
            "200": "examination of complainant",
            "204": "issue of process",
            "207": "supply of copies of police report and other documents to the accused",
            "216": "court's power to alter charge",
            "227": "discharge of accused",
            "228": "framing of charge",
            "239": "when accused shall be discharged",
            "240": "framing of charge in non-summons cases",
            "256": "non-appearance or death of complainant",
            "265A": "plea bargaining",
            "273": "evidence to be taken in presence of accused",
            "300": "person once convicted or acquitted not to be tried for same offence",
            "320": "compounding of offences",
            "357": "order to pay compensation",
            "378": "appeal in case of acquittal",
            "397": "calling for records to exercise powers of revision",
            "401": "high court's powers of revision",
            "436": "in what cases bail to be taken",
            "437": "when bail may be taken in case of non-bailable offence",
            "438": "direction for grant of bail to person apprehending arrest (anticipatory bail)",
            "439": "special powers of high court or court of session regarding bail",
            "482": "saving of inherent powers of high court"
        }
        
        if section in crpc_sections:
            return crpc_sections[section]
        
        return f"a specific provision in the Code of Criminal Procedure"
    
    def _get_cpc_section_info(self, section: str) -> str:
        """Get information about a section of the Civil Procedure Code."""
        # Simplified mapping of common CPC sections
        cpc_sections = {
            "2": "definitions of terms used in the Code",
            "9": "courts to try all civil suits unless barred",
            "10": "stay of suit (res sub judice)",
            "11": "res judicata",
            "13": "when foreign judgment not conclusive",
            "20": "suits to be instituted where defendant resides or cause of action arises",
            "35": "costs",
            "51": "powers of court to enforce execution",
            "80": "notice before filing suit against government",
            "89": "settlement of disputes outside the court",
            "100": "second appeal",
            "115": "revision",
            "144": "application for restitution",
            "148": "enlargement of time",
            "151": "inherent powers of court",
            "152": "amendment of judgments, decrees, or orders",
            "226": "when copies of public documents may be certified"
        }
        
        if section in cpc_sections:
            return cpc_sections[section]
        
        return f"a specific provision in the Code of Civil Procedure"
    
    def _get_constitution_article_info(self, article: str) -> str:
        """Get information about an article of the Indian Constitution."""
        # Simplified mapping of common Articles
        constitution_articles = {
            "12": "definition of 'State'",
            "13": "laws inconsistent with or in derogation of the fundamental rights",
            "14": "equality before law",
            "15": "prohibition of discrimination on grounds of religion, race, caste, sex, or place of birth",
            "16": "equality of opportunity in matters of public employment",
            "19": "protection of certain rights regarding freedom of speech, etc.",
            "20": "protection in respect of conviction for offences",
            "21": "protection of life and personal liberty",
            "21A": "right to education",
            "22": "protection against arrest and detention in certain cases",
            "23": "prohibition of traffic in human beings and forced labour",
            "24": "prohibition of employment of children in factories, etc.",
            "25": "freedom of conscience and free profession, practice, and propagation of religion",
            "26": "freedom to manage religious affairs",
            "29": "protection of interests of minorities",
            "30": "right of minorities to establish and administer educational institutions",
            "32": "remedies for enforcement of fundamental rights",
            "44": "uniform civil code for the citizens",
            "51A": "fundamental duties",
            "72": "power of President to grant pardons, etc. and to suspend, remit or commute sentences in certain cases",
            "74": "Council of Ministers to aid and advise President",
            "124": "establishment and constitution of Supreme Court",
            "131": "original jurisdiction of the Supreme Court",
            "136": "special leave to appeal by the Supreme Court",
            "214": "high courts for states",
            "226": "power of high courts to issue certain writs",
            "245": "extent of laws made by Parliament and by the legislatures of states",
            "246": "subject-matter of laws made by Parliament and by the legislatures of states",
            "352": "proclamation of emergency",
            "356": "provisions in case of failure of constitutional machinery in states",
            "368": "power of Parliament to amend the Constitution and procedure therefor"
        }
        
        if article in constitution_articles:
            return constitution_articles[article]
        
        return "a specific provision in the Indian Constitution"
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history."""
        return self.conversation_history
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []

# Initialize a global chatbot instance
legal_chatbot = LegalChatbot()