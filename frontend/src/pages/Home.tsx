import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useEffect } from 'react';
import AOS from 'aos';
import 'aos/dist/aos.css';
import {
  ChartBarIcon,
  CubeTransparentIcon,
  LightBulbIcon,
  RocketLaunchIcon,
  UserGroupIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline';

const features = [
  {
    name: 'AI-Powered Analysis',
    description: 'Get deep market insights and competitor analysis using advanced AI algorithms.',
    icon: BeakerIcon,
  },
  {
    name: 'Launch Planning',
    description: 'Plan your product launches with comprehensive timelines and milestones.',
    icon: RocketLaunchIcon,
  },
  {
    name: 'Market Research',
    description: 'Access real-time market data and trends to make informed decisions.',
    icon: ChartBarIcon,
  },
  {
    name: 'Competitor Tracking',
    description: 'Monitor competitor activities and analyze their strategies.',
    icon: UserGroupIcon,
  },
  {
    name: 'Success Metrics',
    description: 'Track and measure your launch success with detailed analytics.',
    icon: CubeTransparentIcon,
  },
  {
    name: 'Smart Insights',
    description: 'Get AI-generated recommendations for improving your launch strategy.',
    icon: LightBulbIcon,
  },
];

const testimonials = [
  {
    content: "This platform transformed how we launch products. The AI insights are incredibly valuable.",
    author: "Sarah Johnson",
    role: "Product Manager at TechCorp"
  },
  {
    content: "The competitor analysis feature saved us months of research time.",
    author: "Michael Chen",
    role: "CEO at InnovateCo"
  }
];

const pricing = [
  {
    name: 'Starter',
    price: '$49',
    period: '/month',
    description: 'Perfect for small teams and startups',
    features: [
      'Basic AI analysis',
      'Launch planning tools',
      'Market insights',
      'Email support',
    ],
    cta: 'Start free trial',
    mostPopular: false,
  },
  {
    name: 'Professional',
    price: '$99',
    period: '/month',
    description: 'For growing businesses',
    features: [
      'Advanced AI analysis',
      'Competitor tracking',
      'Custom reports',
      'Priority support',
      'Team collaboration',
    ],
    cta: 'Start free trial',
    mostPopular: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    description: 'For large organizations',
    features: [
      'Full AI capabilities',
      'Custom integrations',
      'Dedicated support',
      'Advanced analytics',
      'Custom training',
    ],
    cta: 'Contact sales',
    mostPopular: false,
  },
];

export default function Home() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    AOS.init({
      duration: 1000,
      once: true,
      easing: 'ease-in-out',
    });
  }, []);

  return (
    <div className="bg-white">
      {/* Header */}
      <header className="fixed w-full bg-white shadow-sm z-50">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" aria-label="Top">
          <div className="w-full py-6 flex items-center justify-between border-b border-indigo-500 lg:border-none">
            <div className="flex items-center">
              <Link to="/" className="flex items-center">
                <img
                  className="h-10 w-auto"
                  src="/logo.svg"
                  alt="Product Launch Planner"
                />
                <span className="ml-2 text-xl font-bold text-gray-900">Launch Planner</span>
              </Link>
              <div className="hidden ml-10 space-x-8 lg:block">
                <Link to="#features" className="nav-link">Features</Link>
                <Link to="#pricing" className="nav-link">Pricing</Link>
                <Link to="#testimonials" className="nav-link">Testimonials</Link>
              </div>
            </div>
            <div className="ml-10 space-x-4">
              <Link to="/login" className="btn btn-secondary">
                Sign in
              </Link>
              <Link to="/signup" className="btn btn-primary">
                Start free trial
              </Link>
            </div>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="relative z-10 pb-8 bg-gray-50 sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">
            <main className="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
              <div className="sm:text-center lg:text-left">
                <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                  <span className="block">Launch Your Products</span>
                  <span className="block text-blue-600">with Confidence</span>
                </h1>
                <p className="mt-3 text-base text-gray-500 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                  Get powerful insights, market analysis, and AI-driven recommendations for your Amazon product launches.
                </p>
                <div className="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start">
                  <div className="rounded-md shadow">
                    <button
                      onClick={() => navigate('/free-trial')}
                      className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 md:py-4 md:text-lg md:px-10"
                    >
                      Start Free Trial
                    </button>
                  </div>
                  <div className="mt-3 sm:mt-0 sm:ml-3">
                    <button
                      onClick={() => navigate('/login')}
                      className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 md:py-4 md:text-lg md:px-10"
                    >
                      Sign In
                    </button>
                  </div>
                </div>
              </div>
            </main>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div id="features" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base text-indigo-600 font-semibold tracking-wide uppercase">Features</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
              Everything you need for successful launches
            </p>
            <p className="mt-4 max-w-2xl text-xl text-gray-500 lg:mx-auto">
              Our platform provides comprehensive tools and insights to help you plan, execute, and track your product launches.
            </p>
          </div>

          <div className="mt-20">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {features.map((feature, index) => (
                <motion.div
                  key={feature.name}
                  initial={{ opacity: 0, y: 50 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  className="relative"
                >
                  <div className="flow-root bg-white px-6 pb-8 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow duration-300">
                    <div className="-mt-6">
                      <div>
                        <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                          <feature.icon className="h-6 w-6 text-white" aria-hidden="true" />
                        </span>
                      </div>
                      <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">{feature.name}</h3>
                      <p className="mt-5 text-base text-gray-500">{feature.description}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Testimonial Section */}
      <div id="testimonials" className="bg-gray-50 pt-16 lg:py-24">
        <div className="pb-16 bg-indigo-600 lg:pb-0 lg:z-10 lg:relative">
          <div className="lg:mx-auto lg:max-w-7xl lg:px-8 lg:grid lg:grid-cols-3 lg:gap-8">
            <div className="relative lg:-my-8">
              <div className="mx-auto max-w-md px-4 sm:max-w-3xl sm:px-6 lg:p-0 lg:h-full">
                <div className="aspect-w-10 aspect-h-6 rounded-xl shadow-xl overflow-hidden sm:aspect-w-16 sm:aspect-h-7 lg:aspect-none lg:h-full">
                  <img
                    className="object-cover lg:h-full lg:w-full"
                    src="/testimonials.jpg"
                    alt="Customer testimonials"
                  />
                </div>
              </div>
            </div>
            <div className="mt-12 lg:m-0 lg:col-span-2 lg:pl-8">
              <div className="mx-auto max-w-md px-4 sm:max-w-2xl sm:px-6 lg:px-0 lg:py-20 lg:max-w-none">
                {testimonials.map((testimonial, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: 50 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5, delay: index * 0.2 }}
                    viewport={{ once: true }}
                    className={`${index > 0 ? 'mt-8' : ''}`}
                  >
                    <blockquote>
                      <div>
                        <p className="text-xl font-medium text-white">
                          "{testimonial.content}"
                        </p>
                      </div>
                      <footer className="mt-3">
                        <div className="flex items-center space-x-3">
                          <div className="text-base font-medium text-white">{testimonial.author}</div>
                          <svg
                            viewBox="0 0 2 2"
                            width={3}
                            height={3}
                            aria-hidden="true"
                            className="fill-white"
                          >
                            <circle cx={1} cy={1} r={1} />
                          </svg>
                          <div className="text-base font-medium text-indigo-100">
                            {testimonial.role}
                          </div>
                        </div>
                      </footer>
                    </blockquote>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Section */}
      <div id="pricing" className="bg-gray-900">
        <div className="pt-12 px-4 sm:px-6 lg:px-8 lg:pt-20">
          <div className="text-center">
            <h2 className="text-lg leading-6 font-semibold text-gray-300 uppercase tracking-wider">Pricing</h2>
            <p className="mt-2 text-3xl font-extrabold text-white sm:text-4xl lg:text-5xl">
              The right price for you, whoever you are
            </p>
            <p className="mt-3 max-w-4xl mx-auto text-xl text-gray-300 sm:mt-5 sm:text-2xl">
              Choose the perfect plan that fits your needs. All plans include a 14-day free trial.
            </p>
          </div>
        </div>

        <div className="mt-16 bg-white pb-12 lg:mt-20 lg:pb-20">
          <div className="relative z-0">
            <div className="absolute inset-0 h-5/6 bg-gray-900 lg:h-2/3" />
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="relative lg:grid lg:grid-cols-3 lg:gap-x-8">
                {pricing.map((tier, index) => (
                  <motion.div
                    key={tier.name}
                    initial={{ opacity: 0, y: 50 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: index * 0.2 }}
                    viewport={{ once: true }}
                    className={`${
                      tier.mostPopular
                        ? 'bg-white ring-2 ring-indigo-600 shadow-xl'
                        : 'bg-white lg:mt-8'
                    } rounded-lg px-6 pb-8 max-w-xl mx-auto mt-8 lg:mt-0`}
                  >
                    <div className="p-8">
                      {tier.mostPopular && (
                        <div className="absolute top-0 p-2 transform -translate-y-1/2 rounded-full bg-indigo-600 text-white text-sm font-semibold tracking-wide shadow-md">
                          Most popular
                        </div>
                      )}
                      <div className="mb-4">
                        <h3 className="text-2xl font-medium leading-6 text-gray-900">{tier.name}</h3>
                        <div className="mt-4 flex items-baseline text-6xl font-extrabold">
                          {tier.price}
                          {tier.period && (
                            <span className="ml-1 text-2xl font-medium text-gray-500">
                              {tier.period}
                            </span>
                          )}
                        </div>
                        <p className="mt-4 text-sm text-gray-500">{tier.description}</p>
                      </div>
                      <ul className="mt-6 space-y-4">
                        {tier.features.map((feature) => (
                          <li key={feature} className="flex space-x-3">
                            <svg
                              className="flex-shrink-0 h-5 w-5 text-green-500"
                              xmlns="http://www.w3.org/2000/svg"
                              viewBox="0 0 20 20"
                              fill="currentColor"
                            >
                              <path
                                fillRule="evenodd"
                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                clipRule="evenodd"
                              />
                            </svg>
                            <span className="text-base text-gray-500">{feature}</span>
                          </li>
                        ))}
                      </ul>
                      <div className="mt-8">
                        <Link
                          to={tier.name === 'Enterprise' ? '/contact' : '/signup'}
                          className={`w-full btn ${
                            tier.mostPopular ? 'btn-primary' : 'btn-secondary'
                          }`}
                        >
                          {tier.cta}
                        </Link>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-700">
        <div className="max-w-2xl mx-auto text-center py-16 px-4 sm:py-20 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
            <span className="block">Ready to boost your sales?</span>
            <span className="block">Start your free trial today.</span>
          </h2>
          <p className="mt-4 text-lg leading-6 text-blue-200">
            No credit card required. 14-day free trial.
          </p>
          <button
            onClick={() => navigate('/free-trial')}
            className="mt-8 w-full inline-flex items-center justify-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-blue-600 bg-white hover:bg-blue-50 sm:w-auto"
          >
            Get started
          </button>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-50" aria-labelledby="footer-heading">
        <h2 id="footer-heading" className="sr-only">
          Footer
        </h2>
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:py-16 lg:px-8">
          <div className="xl:grid xl:grid-cols-3 xl:gap-8">
            <div className="space-y-8 xl:col-span-1">
              <img
                className="h-10"
                src="/logo.svg"
                alt="Product Launch Planner"
              />
              <p className="text-gray-500 text-base">
                Making product launches smarter and more successful with AI-powered insights.
              </p>
              <div className="flex space-x-6">
                {/* Social links */}
                <a href="#" className="text-gray-400 hover:text-gray-500">
                  <span className="sr-only">Twitter</span>
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                  </svg>
                </a>
                <a href="#" className="text-gray-400 hover:text-gray-500">
                  <span className="sr-only">GitHub</span>
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path
                      fillRule="evenodd"
                      d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                      clipRule="evenodd"
                    />
                  </svg>
                </a>
              </div>
            </div>
            <div className="mt-12 grid grid-cols-2 gap-8 xl:mt-0 xl:col-span-2">
              <div className="md:grid md:grid-cols-2 md:gap-8">
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">
                    Product
                  </h3>
                  <ul className="mt-4 space-y-4">
                    <li>
                      <Link to="/features" className="text-base text-gray-500 hover:text-gray-900">
                        Features
                      </Link>
                    </li>
                    <li>
                      <Link to="/pricing" className="text-base text-gray-500 hover:text-gray-900">
                        Pricing
                      </Link>
                    </li>
                    <li>
                      <Link to="/security" className="text-base text-gray-500 hover:text-gray-900">
                        Security
                      </Link>
                    </li>
                  </ul>
                </div>
                <div className="mt-12 md:mt-0">
                  <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">
                    Support
                  </h3>
                  <ul className="mt-4 space-y-4">
                    <li>
                      <Link to="/documentation" className="text-base text-gray-500 hover:text-gray-900">
                        Documentation
                      </Link>
                    </li>
                    <li>
                      <Link to="/guides" className="text-base text-gray-500 hover:text-gray-900">
                        Guides
                      </Link>
                    </li>
                    <li>
                      <Link to="/contact" className="text-base text-gray-500 hover:text-gray-900">
                        Contact
                      </Link>
                    </li>
                  </ul>
                </div>
              </div>
              <div className="md:grid md:grid-cols-2 md:gap-8">
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">
                    Company
                  </h3>
                  <ul className="mt-4 space-y-4">
                    <li>
                      <Link to="/about" className="text-base text-gray-500 hover:text-gray-900">
                        About
                      </Link>
                    </li>
                    <li>
                      <Link to="/blog" className="text-base text-gray-500 hover:text-gray-900">
                        Blog
                      </Link>
                    </li>
                    <li>
                      <Link to="/careers" className="text-base text-gray-500 hover:text-gray-900">
                        Careers
                      </Link>
                    </li>
                  </ul>
                </div>
                <div className="mt-12 md:mt-0">
                  <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">
                    Legal
                  </h3>
                  <ul className="mt-4 space-y-4">
                    <li>
                      <Link to="/privacy" className="text-base text-gray-500 hover:text-gray-900">
                        Privacy
                      </Link>
                    </li>
                    <li>
                      <Link to="/terms" className="text-base text-gray-500 hover:text-gray-900">
                        Terms
                      </Link>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-12 border-t border-gray-200 pt-8">
            <p className="text-base text-gray-400 xl:text-center">
              &copy; 2024 Product Launch Planner. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
} 