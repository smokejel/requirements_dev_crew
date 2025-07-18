from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging
load_dotenv()
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class RequirementDev():
    """RequirementDev crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    
    def _create_llm(self, agent_name: str) -> LLM:
        """
        Create LLM instance based on agent configuration with fallback support.
        
        Args:
            agent_name: Name of the agent to create LLM for
            
        Returns:
            LLM instance configured for the agent
        """
        try:
            llm_config = self.agents_config[agent_name].get('llm_config', {})
            
            # Primary LLM configuration
            primary_llm = LLM(
                model=llm_config.get('model', 'openai/gpt-4o-mini'),
                temperature=llm_config.get('temperature', 0.1),
                max_tokens=llm_config.get('max_tokens', 4000),
                timeout=llm_config.get('timeout', 120)
            )
            
            logging.info(f"Created LLM for {agent_name}: {llm_config.get('model')}")
            return primary_llm
            
        except Exception as e:
            logging.error(f"Failed to create primary LLM for {agent_name}: {e}")
            
            # Fallback LLM configuration
            try:
                fallback_model = llm_config.get('fallback_model', 'openai/gpt-4o-mini')
                fallback_temperature = llm_config.get('fallback_temperature', 0.1)
                
                fallback_llm = LLM(
                    model=fallback_model,
                    temperature=fallback_temperature,
                    max_tokens=llm_config.get('max_tokens', 4000),
                    timeout=llm_config.get('timeout', 120)
                )
                
                logging.warning(f"Using fallback LLM for {agent_name}: {fallback_model}")
                return fallback_llm
                
            except Exception as fallback_error:
                logging.error(f"Fallback LLM creation failed for {agent_name}: {fallback_error}")
                
                # Ultimate fallback - basic configuration
                return LLM(
                    model="openai/gpt-4o-mini",
                    temperature=0.1,
                    max_tokens=4000
                )
    @agent
    def requirements_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['requirements_analyst'], # type: ignore[index]
            llm=self._create_llm('requirements_analyst'),
            verbose=True
        )

    @agent
    def decomposition_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['decomposition_strategist'], # type: ignore[index]
            llm=self._create_llm('decomposition_strategist'),
            verbose=True
        )

    @agent
    def requirements_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['requirements_engineer'], # type: ignore[index]
            llm=self._create_llm('requirements_engineer'),
            verbose=True
        )

    @agent
    def quality_assurance_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['quality_assurance_agent'], # type: ignore[index]
            llm=self._create_llm('quality_assurance_agent'),
            verbose=True
        )

    @agent
    def documentation_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['documentation_specialist'], # type: ignore[index]
            llm=self._create_llm('documentation_specialist'),
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def requirements_extraction_task(self) -> Task:
        return Task(
            config=self.tasks_config['requirements_extraction_task'], # type: ignore[index]
        )

    @task
    def context_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['context_analysis_task'], # type: ignore[index]
        )

    @task
    def strategy_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['strategy_development_task'], # type: ignore[index]
        )

    @task
    def functional_decomposition_task(self) -> Task:
        return Task(
            config=self.tasks_config['functional_decomposition_task'], # type: ignore[index]
        )

    @task
    def nonfunctional_decomposition_task(self) -> Task:
        return Task(
            config=self.tasks_config['nonfunctional_decomposition_task'], # type: ignore[index]
        )

    @task
    def interface_definition_task(self) -> Task:
        return Task(
            config=self.tasks_config['interface_definition_task'], # type: ignore[index]
        )

    @task
    def traceability_task(self) -> Task:
        return Task(
            config=self.tasks_config['traceability_task'], # type: ignore[index]
        )

    @task
    def quality_validation_task(self) -> Task:
        return Task(
            config=self.tasks_config['quality_validation_task'], # type: ignore[index]
        )

    @task
    def documentation_task(self) -> Task:
        return Task(
            config=self.tasks_config['documentation_task'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the RequirementDev crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
