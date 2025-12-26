require 'fileutils'
require 'openssl'

def generate_ca(dir)
  key = OpenSSL::PKey::RSA.new(4096)
  cert = OpenSSL::X509::Certificate.new
  cert.version = 2
  cert.serial = 1
  cert.subject = OpenSSL::X509::Name.parse("/CN=SentinelCA")
  cert.issuer = cert.subject
  cert.public_key = key.public_key
  cert.not_before = Time.now
  cert.not_after = Time.now + 365 * 24 * 60 * 60 # 1 year

  ef = OpenSSL::X509::ExtensionFactory.new
  ef.subject_certificate = cert
  ef.issuer_certificate = cert
  cert.add_extension(ef.create_extension("basicConstraints", "CA:TRUE", true))
  cert.add_extension(ef.create_extension("keyUsage", "keyCertSign, cRLSign", true))
  cert.add_extension(ef.create_extension("subjectKeyIdentifier", "hash", false))
  cert.sign(key, OpenSSL::Digest::SHA256.new)

  File.write("#{dir}/ca.key", key.to_pem)
  File.write("#{dir}/ca.crt", cert.to_pem)
  puts "✅ Generated CA: #{dir}/ca.crt"
  [key, cert]
end

def generate_service_cert(dir, name, ca_key, ca_cert)
  key = OpenSSL::PKey::RSA.new(2048)
  cert = OpenSSL::X509::Certificate.new
  cert.version = 2
  cert.serial = 2
  cert.subject = OpenSSL::X509::Name.parse("/CN=#{name}.sentinel.svc")
  cert.issuer = ca_cert.subject
  cert.public_key = key.public_key
  cert.not_before = Time.now
  cert.not_after = Time.now + 365 * 24 * 60 * 60

  ef = OpenSSL::X509::ExtensionFactory.new
  ef.subject_certificate = cert
  ef.issuer_certificate = ca_cert
  cert.add_extension(ef.create_extension("keyUsage", "digitalSignature, keyEncipherment", true))
  cert.add_extension(ef.create_extension("subjectAltName", "DNS:localhost, DNS:#{name}", false))
  cert.sign(ca_key, OpenSSL::Digest::SHA256.new)

  File.write("#{dir}/#{name}.key", key.to_pem)
  File.write("#{dir}/#{name}.crt", cert.to_pem)
  puts "✅ Generated Cert for #{name}: #{dir}/#{name}.crt"
end

output_dir = "deployment/certs"
FileUtils.mkdir_p(output_dir)

ca_key, ca_cert = generate_ca(output_dir)

services = %w[runtime ai-engine knowledge-graph policy-engine networking logging data-pipeline dashboard]
services.each do |svc|
  generate_service_cert(output_dir, svc, ca_key, ca_cert)
end

puts "\n🚀 All certificates generated successfully in #{output_dir}/"
