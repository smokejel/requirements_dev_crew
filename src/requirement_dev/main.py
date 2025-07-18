#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from requirement_dev.crew import RequirementDev

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the requirements decomposition crew.
    """
    inputs = {
        'primary_specification': 'System Requirements Specification v2.1',
        'target_system': 'Emergency Communication System',
        'decomposition_depth': 'subsystem_level'
    }
    
    try:
        RequirementDev().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the requirements decomposition crew for a given number of iterations.
    """
    inputs = {
        'primary_specification': 'System Requirements Specification v2.1',
        'target_system': 'Emergency Communication System',
        'decomposition_depth': 'subsystem_level'
    }
    try:
        RequirementDev().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        RequirementDev().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the requirements decomposition crew execution and returns the results.
    """
    inputs = {
        'primary_specification': 'System Requirements Specification v2.1',
        'target_system': 'Emergency Communication System',
        'decomposition_depth': 'subsystem_level'
    }
    
    try:
        RequirementDev().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
