import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  const username = 'Bk2026@12';
  const password = '2012@bk2520';
  const email = 'admin@dtunnel.com';

  const passwordHash = bcrypt.hashSync(password, 10);

  const user = await prisma.user.upsert({
    where: { username: username.toLowerCase() },
    update: {
      password: passwordHash,
    },
    create: {
      username: username.toLowerCase(),
      password: passwordHash,
      email,
    },
  });

  console.log({ message: 'Administrador configurado com sucesso', user: user.username });
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
