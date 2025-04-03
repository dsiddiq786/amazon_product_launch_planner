import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PlusIcon, CheckIcon } from '@heroicons/react/24/outline';

interface Plan {
  id: string;
  name: string;
  description: string;
  price: number;
  features: string[];
  isPopular: boolean;
  maxProjects: number;
  maxUsers: number;
}

export default function Plans() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const { data: plans, isLoading } = useQuery<Plan[]>({
    queryKey: ['plans'],
    queryFn: async () => {
      // TODO: Replace with actual API call
      return [
        {
          id: '1',
          name: 'Basic',
          description: 'Perfect for small teams',
          price: 29,
          features: [
            '5 projects',
            '3 team members',
            'Basic analytics',
            'Email support',
          ],
          isPopular: false,
          maxProjects: 5,
          maxUsers: 3,
        },
        {
          id: '2',
          name: 'Pro',
          description: 'Best for growing businesses',
          price: 79,
          features: [
            'Unlimited projects',
            '10 team members',
            'Advanced analytics',
            'Priority support',
            'Custom prompts',
          ],
          isPopular: true,
          maxProjects: -1,
          maxUsers: 10,
        },
        {
          id: '3',
          name: 'Enterprise',
          description: 'For large organizations',
          price: 299,
          features: [
            'Unlimited everything',
            'Custom integrations',
            'Dedicated support',
            'Custom training',
            'SLA guarantee',
          ],
          isPopular: false,
          maxProjects: -1,
          maxUsers: -1,
        },
      ];
    },
  });

  return (
    <div>
      <div className="sm:flex sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Plans</h1>
          <p className="mt-2 text-sm text-gray-700">
            Manage subscription plans and pricing
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsCreateModalOpen(true)}
          className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <PlusIcon className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
          New Plan
        </button>
      </div>

      <div className="mt-12 space-y-4 sm:mt-16 sm:space-y-0 sm:grid sm:grid-cols-2 sm:gap-6 lg:max-w-4xl lg:mx-auto xl:max-w-none xl:grid-cols-3">
        {isLoading ? (
          <div className="col-span-3 text-center text-gray-500 py-12">
            Loading plans...
          </div>
        ) : (
          plans?.map((plan) => (
            <div
              key={plan.id}
              className={`rounded-lg shadow-sm divide-y divide-gray-200 ${
                plan.isPopular
                  ? 'border-2 border-indigo-500'
                  : 'border border-gray-200'
              }`}
            >
              <div className="p-6">
                <h2 className="text-lg leading-6 font-medium text-gray-900">
                  {plan.name}
                </h2>
                <p className="mt-4 text-sm text-gray-500">{plan.description}</p>
                <p className="mt-8">
                  <span className="text-4xl font-extrabold text-gray-900">
                    ${plan.price}
                  </span>
                  <span className="text-base font-medium text-gray-500">/mo</span>
                </p>
                <button
                  type="button"
                  className={`mt-8 block w-full py-2 px-3 border rounded-md text-sm font-semibold text-center ${
                    plan.isPopular
                      ? 'border-indigo-600 bg-indigo-600 text-white hover:bg-indigo-700'
                      : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Edit Plan
                </button>
              </div>
              <div className="pt-6 pb-8 px-6">
                <h3 className="text-xs font-medium text-gray-900 tracking-wide uppercase">
                  What's included
                </h3>
                <ul role="list" className="mt-6 space-y-4">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex space-x-3">
                      <CheckIcon
                        className="flex-shrink-0 h-5 w-5 text-green-500"
                        aria-hidden="true"
                      />
                      <span className="text-sm text-gray-500">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))
        )}
      </div>

      {/* TODO: Add create plan modal */}
    </div>
  );
} 