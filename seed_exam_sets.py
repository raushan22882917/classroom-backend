"""Seed script to populate database with sample PYQ exam sets for all subjects (2015-2024)"""

import asyncio
from datetime import datetime
from supabase import create_client
from app.config import settings
from app.models.base import Subject


# Sample questions for each subject
SAMPLE_QUESTIONS = {
    Subject.MATHEMATICS: [
        {
            "question": "Find the derivative of f(x) = x³ + 2x² - 5x + 7",
            "solution": "f'(x) = 3x² + 4x - 5",
            "marks": 2,
            "difficulty": "easy"
        },
        {
            "question": "Evaluate the integral ∫(2x + 3)dx from 0 to 2",
            "solution": "[x² + 3x] from 0 to 2 = (4 + 6) - 0 = 10",
            "marks": 3,
            "difficulty": "medium"
        },
        {
            "question": "Solve the differential equation dy/dx = x²y with initial condition y(0) = 1",
            "solution": "Separating variables: dy/y = x²dx. Integrating: ln|y| = x³/3 + C. With y(0)=1, C=0. Therefore y = e^(x³/3)",
            "marks": 5,
            "difficulty": "hard"
        },
        {
            "question": "Find the area bounded by the curve y = x² and the line y = 4",
            "solution": "Points of intersection: x² = 4, x = ±2. Area = ∫[-2 to 2](4 - x²)dx = [4x - x³/3] from -2 to 2 = 32/3 square units",
            "marks": 4,
            "difficulty": "medium"
        },
        {
            "question": "If A = [[1, 2], [3, 4]], find A⁻¹",
            "solution": "det(A) = -2. A⁻¹ = (1/-2)[[4, -2], [-3, 1]] = [[-2, 1], [3/2, -1/2]]",
            "marks": 3,
            "difficulty": "medium"
        }
    ],
    Subject.PHYSICS: [
        {
            "question": "State and explain Ohm's law. Draw a circuit diagram to verify it experimentally.",
            "solution": "Ohm's law states that the current through a conductor is directly proportional to the voltage across it, provided temperature remains constant. V = IR, where V is voltage, I is current, and R is resistance. Circuit includes battery, ammeter, voltmeter, rheostat, and resistor.",
            "marks": 3,
            "difficulty": "easy"
        },
        {
            "question": "Derive the expression for the electric field due to an infinite line charge.",
            "solution": "Using Gauss's law, consider a cylindrical Gaussian surface. E·2πrl = λl/ε₀. Therefore E = λ/(2πε₀r), where λ is linear charge density.",
            "marks": 5,
            "difficulty": "hard"
        },
        {
            "question": "A particle moves with velocity v = 3t² + 2t. Find its acceleration at t = 2s.",
            "solution": "Acceleration a = dv/dt = 6t + 2. At t = 2s, a = 6(2) + 2 = 14 m/s²",
            "marks": 2,
            "difficulty": "easy"
        },
        {
            "question": "Explain the photoelectric effect and derive Einstein's photoelectric equation.",
            "solution": "When light of sufficient frequency falls on a metal surface, electrons are emitted. Einstein's equation: hν = φ + KEmax, where hν is photon energy, φ is work function, and KEmax is maximum kinetic energy of emitted electrons.",
            "marks": 4,
            "difficulty": "medium"
        },
        {
            "question": "Calculate the magnetic field at the center of a circular coil of radius 10 cm carrying a current of 5 A.",
            "solution": "B = μ₀I/(2r) = (4π × 10⁻⁷ × 5)/(2 × 0.1) = 3.14 × 10⁻⁵ T",
            "marks": 3,
            "difficulty": "medium"
        }
    ],
    Subject.CHEMISTRY: [
        {
            "question": "Define molarity and molality. Calculate the molarity of a solution containing 4g NaOH in 250 mL solution.",
            "solution": "Molarity = moles/volume(L). Moles of NaOH = 4/40 = 0.1. Volume = 0.25 L. Molarity = 0.1/0.25 = 0.4 M. Molality = moles/mass of solvent(kg).",
            "marks": 3,
            "difficulty": "easy"
        },
        {
            "question": "Explain SN1 and SN2 mechanisms with examples.",
            "solution": "SN1: Unimolecular nucleophilic substitution, two-step mechanism with carbocation intermediate. Rate = k[substrate]. Example: tert-butyl bromide. SN2: Bimolecular, one-step with backside attack. Rate = k[substrate][nucleophile]. Example: methyl bromide.",
            "marks": 5,
            "difficulty": "hard"
        },
        {
            "question": "Write the IUPAC name of CH₃-CH(CH₃)-CH₂-OH",
            "solution": "2-methylpropan-1-ol or isobutanol",
            "marks": 2,
            "difficulty": "easy"
        },
        {
            "question": "Explain the preparation of phenol from benzene sulphonic acid.",
            "solution": "Benzene → Benzene sulphonic acid (H₂SO₄) → Sodium benzene sulphonate (NaOH) → Sodium phenoxide (NaOH fusion at 623K) → Phenol (H⁺/H₂O)",
            "marks": 4,
            "difficulty": "medium"
        },
        {
            "question": "Calculate the pH of 0.01 M HCl solution.",
            "solution": "[H⁺] = 0.01 M = 10⁻² M. pH = -log[H⁺] = -log(10⁻²) = 2",
            "marks": 2,
            "difficulty": "easy"
        }
    ],
    Subject.BIOLOGY: [
        {
            "question": "Explain the structure and function of DNA.",
            "solution": "DNA is a double helix structure with two antiparallel polynucleotide chains. Sugar-phosphate backbone with nitrogenous bases (A, T, G, C) paired via hydrogen bonds. A pairs with T (2 H-bonds), G pairs with C (3 H-bonds). Functions: genetic information storage, replication, and protein synthesis.",
            "marks": 5,
            "difficulty": "medium"
        },
        {
            "question": "What is photosynthesis? Write the overall equation.",
            "solution": "Photosynthesis is the process by which green plants synthesize glucose using sunlight, CO₂, and water. 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂. Occurs in chloroplasts with light and dark reactions.",
            "marks": 3,
            "difficulty": "easy"
        },
        {
            "question": "Describe the process of protein synthesis (translation).",
            "solution": "Translation occurs in ribosomes. mRNA binds to ribosome, tRNA brings amino acids matching codon-anticodon pairs. Peptide bonds form between amino acids. Process continues until stop codon is reached. Polypeptide chain is released and folds into functional protein.",
            "marks": 5,
            "difficulty": "hard"
        },
        {
            "question": "Explain Mendel's law of segregation with a monohybrid cross.",
            "solution": "Law states that allele pairs separate during gamete formation. In F1 generation of Tt × Tt cross: gametes T and t. F2 ratio: 1 TT : 2 Tt : 1 tt (genotypic 1:2:1, phenotypic 3:1).",
            "marks": 4,
            "difficulty": "medium"
        },
        {
            "question": "Name the parts of a typical angiospermic ovule.",
            "solution": "Parts include: nucellus, integuments (inner and outer), micropyle, chalaza, funiculus, hilum, embryo sac with egg cell, synergids, antipodal cells, and polar nuclei.",
            "marks": 3,
            "difficulty": "medium"
        }
    ]
}


async def seed_exam_sets():
    """Seed database with sample PYQ sets for all subjects from 2015-2024"""
    
    print("Connecting to Supabase...")
    supabase = create_client(settings.supabase_url, settings.supabase_service_key)
    
    print("Starting to seed exam sets...")
    
    total_inserted = 0
    
    for subject in Subject:
        print(f"\nSeeding {subject.value} questions...")
        
        questions = SAMPLE_QUESTIONS.get(subject, [])
        
        if not questions:
            print(f"  No sample questions defined for {subject.value}")
            continue
        
        # Create questions for years 2015-2024
        for year in range(2015, 2025):
            print(f"  Creating exam set for year {year}...")
            
            # Insert each question for this year
            for idx, question_data in enumerate(questions):
                pyq_data = {
                    "subject": subject.value,
                    "year": year,
                    "question": question_data["question"],
                    "solution": question_data["solution"],
                    "marks": question_data["marks"],
                    "difficulty": question_data["difficulty"],
                    "metadata": {
                        "question_number": idx + 1,
                        "seeded_at": datetime.utcnow().isoformat()
                    }
                }
                
                try:
                    result = supabase.table("pyqs").insert(pyq_data).execute()
                    
                    if result.data:
                        total_inserted += 1
                    else:
                        print(f"    Warning: Failed to insert question {idx + 1}")
                        
                except Exception as e:
                    print(f"    Error inserting question {idx + 1}: {str(e)}")
            
            print(f"    ✓ Inserted {len(questions)} questions for {year}")
    
    print(f"\n✅ Seeding complete! Total questions inserted: {total_inserted}")
    print(f"   Subjects: {len(Subject)}")
    print(f"   Years: 2015-2024 (10 years)")
    print(f"   Questions per year per subject: ~5")


if __name__ == "__main__":
    asyncio.run(seed_exam_sets())
