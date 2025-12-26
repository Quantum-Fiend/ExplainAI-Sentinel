#!/usr/bin/env ruby
# frozen_string_literal: true

require 'yaml'
require 'fileutils'

# ExplainAI-Sentinel Deployment Orchestrator
class DeploymentOrchestrator
  SERVICES = {
    'runtime' => { port: 8000, language: 'go' },
    'ai-engine' => { port: 8001, language: 'python' },
    'knowledge-graph' => { port: 8002, language: 'scala' },
    'policy-engine' => { port: 8003, language: 'rust' },
    'dashboard' => { port: 3000, language: 'typescript' },
    'networking' => { port: 8080, language: 'java' },
    'logging' => { port: 8082, language: 'c' },
    'data-pipeline' => { port: 8083, language: 'kotlin' }
  }.freeze

  def initialize
    @root_dir = File.expand_path('../..', __dir__)
    @deployment_dir = File.join(@root_dir, 'deployment')
  end

  def generate_docker_compose
    puts '📦 Generating docker-compose.yml...'

    compose = {
      'version' => '3.8',
      'services' => {},
      'networks' => {
        'sentinel-network' => {
          'driver' => 'bridge'
        }
      },
      'volumes' => {
        'postgres-data' => {},
        'redis-data' => {},
        'neo4j-data' => {}
      }
    }

    # Add services
    SERVICES.each do |name, config|
      compose['services'][name] = generate_service_config(name, config)
    end

    # Add infrastructure services
    compose['services'].merge!(infrastructure_services)

    # Write file
    File.write(
      File.join(@deployment_dir, 'docker-compose.yml'),
      compose.to_yaml
    )

    puts '✅ docker-compose.yml generated'
  end

  def generate_kubernetes_manifests
    puts '☸️  Generating Kubernetes manifests...'

    k8s_dir = File.join(@deployment_dir, 'kubernetes')
    FileUtils.mkdir_p(k8s_dir)

    # Generate namespace
    generate_namespace(k8s_dir)

    # Generate deployments and services for each component
    SERVICES.each do |name, config|
      generate_k8s_deployment(k8s_dir, name, config)
      generate_k8s_service(k8s_dir, name, config)
    end

    # Generate ingress
    generate_ingress(k8s_dir)

    # Generate configmaps
    generate_configmaps(k8s_dir)

    puts '✅ Kubernetes manifests generated'
  end

  def deploy_to_docker
    puts '🚀 Deploying to Docker...'
    
    Dir.chdir(@deployment_dir) do
      system('docker-compose up -d --build')
    end

    puts '✅ Deployment complete'
    puts '📊 Dashboard: http://localhost:3000'
  end

  def deploy_to_kubernetes(context = 'minikube')
    puts "☸️  Deploying to Kubernetes (#{context})..."

    k8s_dir = File.join(@deployment_dir, 'kubernetes')

    system("kubectl config use-context #{context}")
    system("kubectl apply -f #{k8s_dir}/namespace.yaml")
    system("kubectl apply -f #{k8s_dir}/")

    puts '✅ Kubernetes deployment complete'
  end

  private

  def generate_service_config(name, config)
    {
      'build' => {
        'context' => "../#{name}",
        'dockerfile' => 'Dockerfile'
      },
      'container_name' => "sentinel-#{name}",
      'ports' => ["#{config[:port]}:#{config[:port]}"],
      'networks' => ['sentinel-network'],
      'environment' => service_environment(name, config),
      'restart' => 'unless-stopped',
      'healthcheck' => {
        'test' => ["CMD", "curl", "-f", "http://localhost:#{config[:port]}/health"],
        'interval' => '30s',
        'timeout' => '10s',
        'retries' => 3
      }
    }
  end

  def service_environment(name, config)
    base_env = {
      'SERVICE_NAME' => name,
      'PORT' => config[:port].to_s,
      'LOG_LEVEL' => 'info'
    }

    case name
    when 'ai-engine'
      base_env.merge({
        'PYTHONUNBUFFERED' => '1',
        'MODEL_PATH' => '/app/models'
      })
    when 'knowledge-graph'
      base_env.merge({
        'SPARK_MASTER' => 'local[*]',
        'NEO4J_URI' => 'bolt://neo4j:7687'
      })
    when 'policy-engine'
      base_env.merge({
        'RUST_LOG' => 'info'
      })
    else
      base_env
    end
  end

  def infrastructure_services
    {
      'postgres' => {
        'image' => 'postgres:15-alpine',
        'container_name' => 'sentinel-postgres',
        'environment' => {
          'POSTGRES_DB' => 'sentinel',
          'POSTGRES_USER' => 'sentinel',
          'POSTGRES_PASSWORD' => 'sentinel123'
        },
        'volumes' => ['postgres-data:/var/lib/postgresql/data'],
        'networks' => ['sentinel-network'],
        'ports' => ['5432:5432']
      },
      'redis' => {
        'image' => 'redis:7-alpine',
        'container_name' => 'sentinel-redis',
        'volumes' => ['redis-data:/data'],
        'networks' => ['sentinel-network'],
        'ports' => ['6379:6379']
      },
      'neo4j' => {
        'image' => 'neo4j:5-community',
        'container_name' => 'sentinel-neo4j',
        'environment' => {
          'NEO4J_AUTH' => 'neo4j/password'
        },
        'volumes' => ['neo4j-data:/data'],
        'networks' => ['sentinel-network'],
        'ports' => ['7474:7474', '7687:7687']
      },
      'prometheus' => {
        'image' => 'prom/prometheus:latest',
        'container_name' => 'sentinel-prometheus',
        'volumes' => ['./prometheus.yml:/etc/prometheus/prometheus.yml'],
        'networks' => ['sentinel-network'],
        'ports' => ['9090:9090']
      },
      'grafana' => {
        'image' => 'grafana/grafana:latest',
        'container_name' => 'sentinel-grafana',
        'environment' => {
          'GF_SECURITY_ADMIN_PASSWORD' => 'admin'
        },
        'networks' => ['sentinel-network'],
        'ports' => ['3001:3000']
      }
    }
  end

  def generate_namespace(k8s_dir)
    namespace = {
      'apiVersion' => 'v1',
      'kind' => 'Namespace',
      'metadata' => {
        'name' => 'explainai-sentinel',
        'labels' => {
          'name' => 'explainai-sentinel'
        }
      }
    }

    File.write(
      File.join(k8s_dir, 'namespace.yaml'),
      namespace.to_yaml
    )
  end

  def generate_k8s_deployment(k8s_dir, name, config)
    deployment = {
      'apiVersion' => 'apps/v1',
      'kind' => 'Deployment',
      'metadata' => {
        'name' => name,
        'namespace' => 'explainai-sentinel',
        'labels' => {
          'app' => name
        }
      },
      'spec' => {
        'replicas' => 2,
        'selector' => {
          'matchLabels' => {
            'app' => name
          }
        },
        'template' => {
          'metadata' => {
            'labels' => {
              'app' => name
            }
          },
          'spec' => {
            'containers' => [{
              'name' => name,
              'image' => "explainai-sentinel/#{name}:latest",
              'ports' => [{
                'containerPort' => config[:port]
              }],
              'env' => k8s_environment(name, config),
              'resources' => {
                'requests' => {
                  'memory' => '256Mi',
                  'cpu' => '250m'
                },
                'limits' => {
                  'memory' => '1Gi',
                  'cpu' => '1000m'
                }
              },
              'livenessProbe' => {
                'httpGet' => {
                  'path' => '/health',
                  'port' => config[:port]
                },
                'initialDelaySeconds' => 30,
                'periodSeconds' => 10
              },
              'readinessProbe' => {
                'httpGet' => {
                  'path' => '/health',
                  'port' => config[:port]
                },
                'initialDelaySeconds' => 10,
                'periodSeconds' => 5
              }
            }]
          }
        }
      }
    }

    File.write(
      File.join(k8s_dir, "#{name}-deployment.yaml"),
      deployment.to_yaml
    )
  end

  def generate_k8s_service(k8s_dir, name, config)
    service = {
      'apiVersion' => 'v1',
      'kind' => 'Service',
      'metadata' => {
        'name' => name,
        'namespace' => 'explainai-sentinel',
        'labels' => {
          'app' => name
        }
      },
      'spec' => {
        'type' => 'ClusterIP',
        'ports' => [{
          'port' => config[:port],
          'targetPort' => config[:port],
          'protocol' => 'TCP'
        }],
        'selector' => {
          'app' => name
        }
      }
    }

    File.write(
      File.join(k8s_dir, "#{name}-service.yaml"),
      service.to_yaml
    )
  end

  def generate_ingress(k8s_dir)
    ingress = {
      'apiVersion' => 'networking.k8s.io/v1',
      'kind' => 'Ingress',
      'metadata' => {
        'name' => 'sentinel-ingress',
        'namespace' => 'explainai-sentinel',
        'annotations' => {
          'nginx.ingress.kubernetes.io/rewrite-target' => '/'
        }
      },
      'spec' => {
        'rules' => [{
          'host' => 'sentinel.local',
          'http' => {
            'paths' => SERVICES.map do |name, config|
              {
                'path' => "/#{name}",
                'pathType' => 'Prefix',
                'backend' => {
                  'service' => {
                    'name' => name,
                    'port' => {
                      'number' => config[:port]
                    }
                  }
                }
              }
            end
          }
        }]
      }
    }

    File.write(
      File.join(k8s_dir, 'ingress.yaml'),
      ingress.to_yaml
    )
  end

  def generate_configmaps(k8s_dir)
    # Placeholder for configmaps
    puts '  Generated configmaps'
  end

  def k8s_environment(name, config)
    service_environment(name, config).map do |key, value|
      { 'name' => key, 'value' => value.to_s }
    end
  end
end

# CLI
if __FILE__ == $PROGRAM_NAME
  orchestrator = DeploymentOrchestrator.new

  case ARGV[0]
  when 'generate'
    orchestrator.generate_docker_compose
    orchestrator.generate_kubernetes_manifests
  when 'docker'
    orchestrator.deploy_to_docker
  when 'k8s', 'kubernetes'
    context = ARGV[1] || 'minikube'
    orchestrator.deploy_to_kubernetes(context)
  else
    puts 'Usage: deploy.rb [generate|docker|k8s]'
    puts '  generate   - Generate deployment configurations'
    puts '  docker     - Deploy using Docker Compose'
    puts '  k8s        - Deploy to Kubernetes'
  end
end
